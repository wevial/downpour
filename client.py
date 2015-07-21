import tracker
import socket
import struct
import peer

class Client:
    def __init__(self, metainfo, tracker):
        self.metainfo = metainfo
        self.tracker = tracker
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
        self.handshake = handshake
    
    def send_handshake(self, peer):
        peer.connect()
        print 'You have connected!'
        try:
            peer.sendall(self.handshake)
            peer_handshake = ''
            amount_received = 0
            amount_expected = 68 # handshake string length
            while amount_received < amount_expected:
                data = peer.recv(68)
                peer_handshake += data
                amount_recieved += len(data)
        finally:
            print peer_handshake
            return peer_handshake

    def parse_handshake(self, handshake):
        # lenpstr - pstr - reserved - info hash - peer id
        (pstrlen, pstr, peer_hash, peer_id) = struct.unpack('B19s8x20s20s', handshake)
        assert peer_hash == self.tracker.params['info_hash']
        return True

        
    def receive_msg(self):
        pass

