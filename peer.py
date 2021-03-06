import time
import socket
import struct
from bitstring import BitArray
from message import *
import Queue
import logging

REQUESTS_PER_PEER = 5


class Peer:

    def __init__(self, ip, port, client):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.am_choking_peer = True
        self.peer_is_choking_client = True
        self.am_interested = False
        self.peer_is_interested = False
        self.buf = ''  # Data buffer
        self.time_last_msg_received = time.time()
        self.time_last_msg_sent = 0.0
        self.is_alive = False
        self.client = client
        self.bitfield = BitArray(length=client.num_pieces)
        self.msg_queue = Queue.Queue()
        self.outstanding_requests = []
        self.request_q = [] 

    def __repr__(self):
        return str((self.ip, self.port))

    # This feels kind of cheap...
    def __cmp__(self, other):
        return len(self.request_q) - len(other.request_q) 

    # WRAPPER METHODS FOR SOCKET - these are only necessary bc of handshake
    # TODO: refactor handshake into reactor
    def close(self):
        self.socket.close()

    def connect(self):
        logging.debug('Attempting to connect to peer %s', self)
        try:
            self.socket.connect((self.ip, self.port))
        except Exception as e:
            logging.info('Failed to connect to peer %s', self)
            raise e
        else:
            logging.debug('You have connected to peer %s', self)

    def sendall(self, msg_bytes):
        self.socket.sendall(msg_bytes)

    def receive_data(self, amount_expected, block_size):
        logging.debug('Waiting for handshake')
        amount_received = 0
        data = ''
        while amount_received < amount_expected:
            try:
                new_data = self.socket.recv(block_size)
                logging.info('Received %s bytes from peer', len(new_data))
                amount_received += len(new_data)
                data += new_data
            except Exception as e:
                logging.debug('Problem with handshake socket')
                pass
        return data

    def send_message(self, message):
        bytes_to_send = Msg.get_buffer_from_message(message)
        self.sendall(bytes_to_send)

    def connect(self):
        logging.debug('Attempting to connect to peer %s', self)
        try:
            self.socket.settimeout(5.0)
            self.socket.connect((self.ip, self.port))
        except Exception as e:
            logging.info('Failed to connect to peer %s', self)
            raise e
        else:
            logging.debug('You have connected to peer %s', self)

    def send_and_receive_handshake(self, handshake):
        try:
            logging.info('Sending handshake')
#            logging.info('handshake: %s', handshake)
            self.sendall(handshake)
            logging.info('Handshake sent, receiving data')
            peer_handshake = self.receive_data(68, 68)
            logging.info('Peer handshake received.')
        except Exception as e:
            raise e
        else:
            logging.debug('Returning peer handshake')
            return peer_handshake

    def verify_handshake(self, handshake, info_hash):
        # lenpstr - pstr - reserved - info hash - peer id
        (pstrlen, pstr, peer_hash, peer_id) = struct.unpack('B19s8x20s20s', handshake)
        self.peer_id = peer_id
        return peer_hash == info_hash

    # TODO: Clean up handling of block messages here to ONLY send block bytes

    def process_and_act_on_incoming_data(self, data):
        (messages, buf_remainder) = Msg.get_messages_from_buffer(self.buf + data)
        logging.debug('Converting %s bytes from buffer and %s bytes from reactor',
                       len(self.buf), len(data))
        self.act_on_messages(messages)
        self.update_buffer(buf_remainder)
    
    # TODO: Set up message queue to maximize bytes per trip over the servers.

    def act_on_messages(self, messages):
        message_actions = {
            -1: (self.keep_alive, []),
            # Use partial/bound functions for these 3
            0: (self.peer_starts_choking_client, []),
            1: (self.peer_stops_choking_client, []),
            2: (self.peer_is_now_interested, []),
            3: (self.peer_is_no_longer_interested, []),
            4: (self.update_bitfield, ['piece_index']),
            5: (self.setup_bitfield, ['buffer_to_send']),
            6: (self.queue_up_block, ['block_info']),
            7: (self.update_and_store_block, ['block_info', 'buffer_to_send']),
            8: (self.clear_requests, ['block_info']),
            }

        for msg in messages:
            (message_action, message_params) = message_actions[msg.msg_id]
            message_args = [getattr(msg, param) for param in message_params]
            message_action(*message_args)
            self.update_time_last_msg_received()

    def update_buffer(self, buf):
        self.buf = buf

    def update_time_last_msg_received(self):
        self.time_last_msg_received = time.time()
        # TODO: Account for when peer is no longer alive and deal accordingly

    def update_time_last_msg_sent(self):
        self.time_last_msg_sent = time.time()

    def check_if_client_will_time_out(self):
        """ Check to see if client needs to send a keep alive message to avoid
            getting timedout. If its been over 60 seconds, send a keep alive
            message to peer. """
        current_time = time.time()
        return (current_time - self.time_last_msg_sent) > 60.0

    def send_keep_alive(self):
        logging.info('Sending keep alive message to %s', self)
        return KeepAliveMsg().get_buffer_from_message()

    # Upon message id -1
    def keep_alive(self):
        self.time_last_msg_received = time.time()
        self.is_alive = True

    def check_is_still_alive(self):
        time_elapsed = time.time() - self.time_last_msg_received
        self.is_alive = time_elapsed < 120  # Timeout timer set at 2 mins
        return self.is_alive

    def destroy_peer(self):
        logging.info('Peer %s is now DEAD', self)
        for block_info in self.outstanding_requests:
            self.outstanding_requests.remove(block_info)
            self.client.request_block(block_info)
        for block_info in self.request_q:
            self.request_q.remove(block_info)
            self.client.request_block(block_info)
        self.is_alive = False

    def peer_starts_choking_client(self):
        self.peer_is_choking_client = True
        # TODO: Add check for choked status before sending new requests

    def peer_stops_choking_client(self):
        self.peer_is_choking_client = False
        if self.am_interested:
            logging.info('Peer unchoked, sending requests now')
            if len(self.request_q) > 0:
                self.flush_request_queue()
            else:
                # TODO: Trace code path here
                self.client.manage_requests(REQUESTS_PER_PEER)

    def peer_is_now_interested(self):
        self.peer_is_interested = True
        # Assuming we always unchoke when receiving interested message
        self.am_choking_peer = False
        self.add_to_message_queue(UnchokeMsg())

    def peer_is_no_longer_interested(self):
        self.peer_is_interested = False
        # TODO: Update request q based on this information

    # When receiving bitfield
    def setup_bitfield(self, bitfield_buf):
        # TODO implement non-naive function for updating interested status
        bitfield = BitArray(bytes=bitfield_buf)
        self.bitfield = bitfield
        for piece_index, bit in enumerate(bitfield):
            if bit:
                self.client.add_peer_to_piece_peer_list(piece_index, self)
        self.am_interested = True
        self.add_to_message_queue(InterestedMsg())
        self.client.manage_requests(1)

    # When receiving have message
    def update_bitfield(self, piece_index):
        if not self.bitfield[piece_index]:
            self.bitfield.invert(piece_index)
            self.client.add_peer_to_piece_peer_list(piece_index, self)
        else:
            raise PeerCommunicationError('Redundant "Have" message.')

    # After request
    def queue_up_block(self, block_info):
        assert not self.am_choking_peer
        block = self.client.get_block(block_info)
        self.add_to_message_queue(BlockMsg(block_info=block_info, block=block))

    # After block message
    def update_and_store_block(self, block_info, block):
        self.outstanding_requests.remove(block_info)
        self.flush_request_queue()
        logging.debug('Storing block length %s beginning at index %s for piece %s',
                block_info[2], block_info[1], block_info[0])
        logging.debug('Actual length of block: %s', len(block))
        if self.client.torrent_state == 'endgame':
            piece = self.client.pieces[block_info[0]]
            piece.cancel_block(block_info, self)
        self.client.add_block(block_info, block)

    # After cancel message
    def clear_requests(self, block_info):
        pass

    def add_request_to_queue(self, block_info):
        if not self.peer_is_choking_client and \
        len(self.outstanding_requests) < REQUESTS_PER_PEER:
            self.send_request_message(block_info)
        else:
            logging.info('Adding block %s to request q', block_info)
            self.request_q.insert(0, block_info)

    def send_cancel_message(self, block_info):
        self.add_to_message_queue(CancelMsg(block_info))

    def send_request_message(self, block_info):
        self.outstanding_requests.append(block_info)
        logging.info('Sending request for block %s', block_info)
        self.add_to_message_queue(RequestMsg(block_info))

    def flush_request_queue(self):
        '''Move requests from holding queue to reactor message queue'''
        logging.info('Can flush up to %s requests', REQUESTS_PER_PEER - len(self.outstanding_requests))
        logging.info('Request q has %s blocks', len(self.request_q))
        while len(self.outstanding_requests) < REQUESTS_PER_PEER and \
            len(self.request_q) > 0:
            next_block_info = self.request_q.pop()
            logging.info('popped block %s off request q', next_block_info)
            self.send_request_message(next_block_info)

    # MESSAGE QUEUE
    def add_to_message_queue(self, msg):
        logging.info('adding message %s to queue', msg)
        self.msg_queue.put(msg)
        # TODO: Make time last msg sent update when its sent, not added to queue
        self.update_time_last_msg_sent()

    def get_from_message_queue(self):
        if self.msg_queue.empty():
            raise Queue.Empty
        else:
            return self.msg_queue.get_nowait()
