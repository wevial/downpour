import tracker
import struct
import peer
import message
from bitstring import BitArray

class Client:
    def __init__(self, metainfo, tracker):
        self.metainfo = metainfo
        self.tracker = tracker
        self.peer_id = tracker.params['peer_id']
        self.info_hash = tracker.params['info_hash']
        self.pieces = BitArray(len(metainfo.piece_hashes))

    def build_handshake(self):
        pstr = 'BitTorrent protocol'
        handshake = struct.pack('B' + str(len(pstr)) + 's8x20s20s',
                # In format string: 8x => reserved null bytes
                len(pstr),
                pstr,
                self.info_hash,
                self.peer_id
                )
        assert len(handshake) == 49 + len(pstr)
        self.handshake = handshake
    
    def send_and_receive_handshake(self, peer):
        peer.connect()
        print 'You have connected to your peer!'
        peer.sendall(self.handshake)
        peer_handshake = message.receive_data(peer, amount_expected=68, block_size=68)
        return peer_handshake

    def verify_handshake(self, handshake):
        # lenpstr - pstr - reserved - info hash - peer id
        (pstrlen, pstr, peer_hash, peer_id) = struct.unpack('B19s8x20s20s', handshake)
        return peer_hash == self.info_hash
        
    def receive_peer_msg(self, peer):
#        peer_msg = message.receive_data(peer, amount_expected=5, block_size=5)
        length_prefix
        msg_id
        payload

def peer_has_piece():
    pass

def choke_peer():
    pass

def unchoke_peer():
    pass

def request_piece_from_peer():
    pass



