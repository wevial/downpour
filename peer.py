import time
import socket
from bitstring import BitArray
import message
import struct 
from message import Msg

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
    def send_message(self, Msg):
        bytes_to_send = Msg.get_buffer_from_message()
        self.sendall(bytes_to_send) 

    def verify_handshake(self, handshake, info_hash):
        # lenpstr - pstr - reserved - info hash - peer id
        (pstrlen, pstr, peer_hash, peer_id) = struct.unpack('B19s8x20s20s', handshake)
        self.peer_id = peer_id
        return peer_hash == info_hash

    def initiate_messages(self, handshake, info_hash):
        if self.verify_handshake(handshake, info_hash):
            self.send_message(message.Msg(2))
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

    def convert_bytes_to_messages(self, data):
        (messages, buf) = Msg.get_messages_from_buffer(self.buf + data)
        self.act_on_messages(messages)
        self.update_buffer(buf)

    def act_on_messages(self, messages):
        message_handlers = {
                -1: self.keep_alive,
                # Use partial/bound functions for these 3
                0: self.set_flag, # bind flag_id = 0,
                1: self.set_flag, # (flag_id = 1),
                2: self.set_flag, # (flag_id = 2),
                3: self.set_flag, # (flag_id = 3),
                4: self.update_bitfield, # bind bitfield from message
                5: self.set_bitfield, # bind piece_index from message
                6: self.queue_up_block, # bind block_info from message
                7: self.update_and_store_block, # bind block from message
                8: self.clear_requests 
                }
                
        for message in messages:
            # Call message handler with arguments from message
            print message.msg_name
            # How could we make this more modular?
            # Maybe the functions could be class methods for the message classes

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
    def set_flag(self, flag_id):
        if flag_id == 0:
            self.peer_is_choking_client = True
        if flag_id == 1:
            self.peer_is_choking_client = False
            if self.am_interested:
                self.send_message(message.requestMsg(self.client.select_request()))
        if flag_id == 2:
            self.peer_is_interested = True
            # Assuming we always unchoke when receiving interested message
            self.am_choking_peer = False
            self.send_message(message.Msg(1))
        if flag_id == 3:
            self.peer_is_interested = False

    #When receiving bitfield
    def set_bitfield(self, bitfield_buf):
        self.bitfield = BitArray(bytes=bitfield_buf) 
        self.client.update_pieces_count(self.peer_id, self.bitfield)

    #When receiving have message
    def update_bitfield(self, piece_index):
        if not self.bitfield[ piece_index ]:
            self.bitfield.invert(piece_index)
            self.client.increment_piece_count(piece_index, self.peer_id)
        else:
            raise PeerCommunicationError('redundant have message')

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
        





    
