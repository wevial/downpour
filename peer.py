import time
import socket
from bitstring import BitArray
import message
import struct 

class Peer:
    def __init__(self, ip, port):
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
        #Hardcoding length for testing, but this needs to change
        self.bitfield = BitArray(length=20)
        
    def __repr__(self):
        return str((self.ip, self.port))

    def connect(self):
        self.socket.connect((self.ip, self.port))

    def sendall(self, msg_bytes):
        self.socket.sendall(msg_bytes)

    def recv(self, num_bytes):
        return self.socket.recv(num_bytes)

    # TODO: Set up message queue to maximize bytes per trip over the servers.
    def send_message(self, message):
        bytes_to_send = Msg.get_buffer_from_message(message)
        self.sendall(bytes_to_send) 

    def verify_handshake(self, handshake, info_hash):
        # lenpstr - pstr - reserved - info hash - peer id
        (pstrlen, pstr, peer_hash, peer_id) = struct.unpack('B19s8x20s20s', handshake)
        self.peer_id = peer_id
        return peer_hash == info_hash

    def initiate_messages(self, handshake, info_hash):
        if self.verify_handshake(handshake, info_hash):
            self.send_message(message.InterestedMsg())
        else:
            raise ConfirmationError('peer handshake does not match info hash')

    def send_and_receive_handshake(self, handshake):
        self.connect()
        print 'You have connected to your peer!'
        self.sendall(handshake)
        print 'Sending handshake to peer...'
        peer_handshake = message.receive_data(self, amount_expected=68, block_size=68)
        print 'Peer handshake has been received.'
        return peer_handshake

    def process_and_act_on_incoming_data(self, data):
        (messages, buf_remainder) = Msg.get_messages_from_buffer(self.buf + data)
        #(messages, buf) = message.Msg.get_messages_from_buffer(self.buf + data)
        self.act_on_messages(messages)
        self.update_buffer(buf_remainder)

    def act_on_messages(self, messages):
        message_actions = {
                -1: (self.keep_alive, []),
                # Use partial/bound functions for these 3
                0: (self.peer_starts_choking_client, []), 
                1: (self.peer_stops_choking_client, []),
                2: (self.peer_is_now_interested, []),
                3: (self.peer_is_no_longer_interested, []),
                4: (self.update_bitfield, ['bitfield_buf']),
                5: (self.setup_bitfield, ['piece_index']), 
                6: (self.queue_up_block, ['block_info']),
                7: (self.update_and_store_block, ['block_info', 'block']),
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

    #Upon message id 0-3
    def peer_starts_choking_client(self):
        self.peer_is_choing_client = True

    def peer_stops_choking_client(self):
        self.peer_is_choking_client = False
        if self.am_interested:
            self.send_message(message.requestMsg(self.client.select_request()))

    def peer_is_now_interested(self):
        self.peer_is_interested = True
        # Assuming we always unchoke when receiving interested message
        self.am_choking_peer = False
        self.send_message(message.Msg(1))

    def peer_is_no_longer_interested(self):
        self.peer_is_interested = False

    #When receiving bitfield
    def setup_bitfield(self, bitfield_buf):
        self.bitfield = BitArray(bytes=bitfield_buf) 
        self.client.update_pieces_count(self.peer_id, self.bitfield)

    #When receiving have message
    def update_bitfield(self, piece_index):
        if not self.bitfield[piece_index]:
            self.bitfield.invert(piece_index)
            self.client.increment_piece_count(piece_index, self.peer_id)
        else:
            raise PeerCommunicationError('Redundant "Have" message.')

    #After request
    def queue_up_block(self, block_info):
        assert not self.am_choking_peer
        block = self.client.get_block(block_info)
        self.send_message(message.blockMsg(7, block_info = block_info, block = block))

    #After block message
    def update_and_store_block(self, block_info, block):
        self.client.update_block_info(block_info)
        self.client.write_block_to_file(block_info, block)

    # After cancel message
    # TODO
    def clear_requests(self, block_info):
        print 'clear them all'
        





    
