import tracker
import hashlib as H
import bencode as B
import struct
import peer
import message
import tracker

from textwrap import wrap
TEST_TORRENT = 'flagfromserverorig.torrent'

class Client:
    def __init__(self, torrent):
        #Initialize all data from torrent on client object
        self.decode_torrent(torrent)
        #Get info from tracker
         
        self.client_id = '-TZ-0000-00000000000',
        self.tracker = Tracker(self)
        self.peers = {}

    def decode_torrent(self, torrent):
        f = open(torrent, 'r')
        metainfo = B.bdecode(f.read())
        self.tracker_url = metainfo['announce']
        data = metainfo['info'] # Un-bencoded dictionary
        self.info_hash =  H.sha1(B.bencode(data)).digest()
        self.piece_length = data['piece_length']
        self.piece_hashes = wrap(data['pieces'], 20)
        # Currently only worrying about ONE FILE torrents
        # Would have to change these for multi-file
        self.file_name = data['name']
        self.file_length = data['length']
    
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

    def add_peer(id, peer):
        self.peers[id] = peer
        
    def receive_peer_msg(self, peer):
        peer_msg = message.receive_data(peer, amount_expected=5, block_size=5)

def peer_has_piece():
    pass

def choke_peer():
    pass

def unchoke_peer():
    pass

def request_piece_from_peer():
    pass



