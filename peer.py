import socket

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
        
    def __repr__(self):
        return str((self.ip, self.port))

    def connect(self):
        self.socket.connect((self.ip, self.port))

    def sendall(self, msg):
        self.socket.sendall(msg)

    def recv(self, num_bytes):
        return self.socket.recv(num_bytes)

    def has_piece(self):
        pass
