import time
import socket
import struct 
from bitstring import BitArray
from message import *
import Queue

class Peer:
    def __init__(self, ip, port, client):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.am_choking_peer = True
        self.peer_is_choking_client = True
        self.am_interested = False
        self.peer_is_interested = False
        self.buf = '' # Data buffer
        self.time_of_last_msg = time.time()
        self.is_alive = False
        self.client = client
        self.num_pieces = client.num_pieces
        self.bitfield = BitArray(length=self.num_pieces)
        self.msg_queue = Queue.Queue()
        
    def __repr__(self):
        return str((self.ip, self.port))

    ###### WRAPPER METHODS FOR SOCKET ######
    def connect(self):
        self.socket.connect((self.ip, self.port))

    def sendall(self, msg_bytes):
        self.socket.sendall(msg_bytes)

    def recv(self, num_bytes):
        return self.socket.recv(num_bytes)
    ########################################

    # TODO: Set up message queue to maximize bytes per trip over the servers.
    def send_message(self, message):
        bytes_to_send = Msg.get_buffer_from_message(message)
        self.sendall(bytes_to_send) 

    def verify_handshake(self, handshake, info_hash):
        # lenpstr - pstr - reserved - info hash - peer id
        (pstrlen, pstr, peer_hash, peer_id) = struct.unpack('B19s8x20s20s', handshake)
        self.peer_id = peer_id
        return peer_hash == info_hash

    def verify_and_initiate_communication(self, handshake, info_hash):
        if self.verify_handshake(handshake, info_hash):
            self.add_to_message_queue(InterestedMsg())
        else:
            raise ConfirmationError('peer handshake does not match info hash')

    def send_and_receive_handshake(self, handshake):
        self.connect()
        print 'You have connected to your peer!'
        self.sendall(handshake)
        print 'Sending handshake to peer...'
        peer_handshake = receive_data(self, amount_expected=68, block_size=68)
        print 'Peer handshake has been received.'
        return peer_handshake

    def process_and_act_on_incoming_data(self, data):
        (messages, buf_remainder) = Msg.get_messages_from_buffer(self.buf + data)
        self.act_on_messages(messages)
        print 'updating buffer with leftover bytes'
        self.update_buffer(buf_remainder)

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
            # Call message handler with arguments from message
            (message_action, message_params) = message_actions[msg.msg_id]
            message_args = [getattr(msg, param) for param in message_params] 
            message_action(*message_args)

    def update_buffer(self, buf):
        self.buf = buf

    def update_time_of_last_msg(self):
        self.time_of_last_msg = time.time()

    #Upon message id -1
    def keep_alive(self):
        self.time_of_last_msg = time.time()
        self.is_alive = True
        
    def check_is_still_alive(self):
        time_elapsed = time.time() - self.time_of_last_msg
        self.is_alive = time_elapsed < 120 # Timeout timer set at 2 mins
        return self.is_alive

    def peer_starts_choking_client(self):
        self.peer_is_choing_client = True

    def peer_stops_choking_client(self):
        self.peer_is_choking_client = False
        print 'unchoking self!'
        if self.am_interested:
            print 'requesting pieces now'
            self.client.start_pieces_in_order_strategy()

    def peer_is_now_interested(self):
        self.peer_is_interested = True
        # Assuming we always unchoke when receiving interested message
        self.am_choking_peer = False
        self.add_to_message_queue(UnchokeMsg())

    def peer_is_no_longer_interested(self):
        self.peer_is_interested = False

    #When receiving bitfield
    def setup_bitfield(self, bitfield_buf):
        print 'setting up bitfield'
        print 'updating interested status'
        #TODO implement non-naive function for updating interested status
        self.am_interested = True
        bitfield = BitArray(bytes=bitfield_buf) 
        self.bitfield = bitfield
        for piece_index, bit in enumerate(bitfield):
            if bit:
                self.client.add_peer_to_piece_peer_list(piece_index, self)

    #When receiving have message
    def update_bitfield(self, piece_index):
        print 'updating bitfield'
        if not self.bitfield[ piece_index ]:
            self.bitfield.invert(piece_index)
            self.client.add_peer_to_piece_peer_list(piece_index, self)
        else:
            raise PeerCommunicationError('Redundant "Have" message.')

    #After request
    def queue_up_block(self, block_info):
        assert not self.am_choking_peer
        block = self.client.get_block(block_info)
        self.add_to_message_queue(BlockMsg(block_info = block_info, block = block))

    #After block message
    def update_and_store_block(self, block_info, block):
        self.client.write_block_to_file(block_info, block)


    # After cancel message
    # TODO
    def clear_requests(self, block_info):
        print 'clear them all'

    # MESSAGE QUEUE
    def add_to_message_queue(self, msg):
        print 'adding message ', msg, ' to queue'
        self.msg_queue.put(msg)

    def get_from_message_queue(self):
        if self.msg_queue.empty():
            raise Queue.Empty
        else:
            return self.msg_queue.get_nowait()
    





    
