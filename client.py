import tracker
import socket
import sys
import struct

class Client:
    def __init__(self, tracker, metadata):
        self.tracker = tracker
        self.metadata = metadata
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_peer(self, peer):
        self.socket.connect(peer)
        print 'we are connected'

    def build_handshake(self):
        pstr = 'BitTorrent protocol'
        info_hash = self.tracker.params['info_hash']
        peer_id = self.tracker.params['peer_id']
        handshake = struct.pack('B' + str(len(pstr)) + 's8x20s20s', # 8x -> reserved null bytes
                len(pstr),
                pstr,
                info_hash,
                peer_id
                )
        assert len(handshake) == 49 + len(pstr)
        return handshake
    
    def send_handshake(self, peer):
        self.connect_to_peer(peer)
        handshake = self.build_handshake()
        try:
            self.socket.sendall(handshake)
            peer_handshake = ''
            amount_received = 0
            amount_expected = 68 # handshake string length
            while amount_received < amount_expected:
                data = self.socket.recv(68)
                peer_handshake += data
                amount_recieved += len(data)
        finally:
            print peer_handshake
            return peer_handshake
