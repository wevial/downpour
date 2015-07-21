import socket

class Peer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.choked = True
        self.interested = False

    def connect(self):
        self.socket.connect((self.ip, self.port))

    def sendall(self, msg):
        self.socket.sendall(msg)

    def recv(self, num_bytes):
        return self.socket.recv(num_bytes)

    def have_piece(self):
        pass
