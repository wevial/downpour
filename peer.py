import time
import socket
from bitstring import BitArray

class Peer:
    def __init__(self, ip, port, num_pieces):
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
        self.bitfield = BitArray(length=num_pieces)
        
    def __repr__(self):
        return str((self.ip, self.port))

    def connect(self):
        self.socket.connect((self.ip, self.port))

    def sendall(self, msg):
        self.socket.sendall(msg)

    def recv(self, num_bytes):
        return self.socket.recv(num_bytes)

    def update_time_of_last_msg(self):
        self.time_of_last_msg = time.time()

    def continue_living(self):
        self.time_of_last_msg = time.time()
        self.is_alive = True
        
    def check_is_still_alive(self):
        time_elapsed = time.time() - self.time_of_last_msg
        self.is_alive = time_elapsed < 120 # Timeout timer set at 2 mins
        return self.is_alive

    def set_bitfield(self, bitfield_buf):
        self.bitfield = BitArray(bytes=bitfield_buf) 

    def update_bitfield(self, piece_index):
        if not self.bitfield[ piece_index ]:
            self.bitfield.invert(piece_index)

    def set_flag(self, flag):
        if flag == 'choke':
            self.peer_is_choking_client = True
        if flag == 'unchoke': 
            self.peer_is_choking_client = False
            if self.am_interested:
                self.client.send_request(peer, self.select_request())
        if flag == 'interested':
            self.peer_is_interested = True
            # Assuming we always unchoke when receiving interested message
            self.am_choking_peer = False
            self.send_message('unchoke')
        if flag == 'uninterested':
            peer.peer_is_interested = False

    def has_piece(self):
        pass
