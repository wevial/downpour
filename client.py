import hashlib as H
import bencode as B
import struct
from bitstring import BitArray
from textwrap import wrap

from tracker import Tracker
#import peer
import message

TEST_TORRENT = 'flagfromserverorig.torrent'

class Client:
    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_id = '-TZ-0000-00000000000'
        self.peers = {}

    def decode_torrent(self):
        f = open(self.torrent, 'r')
        metainfo = B.bdecode(f.read())
        self.announce_url = metainfo['announce']
        metainfo_data = metainfo['info'] # Un-bencoded dictionary
#        print metainfo_data
        self.info_hash = H.sha1(B.bencode(metainfo_data)).digest()
        self.piece_length = metainfo_data['piece length']
        self.piece_hashes = wrap(metainfo_data['pieces'], 20)
        # Currently only worrying about ONE FILE torrents
        # Would have to change these for multi-file
        self.file_name = metainfo_data['name']
        self.left = metainfo_data['length']

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
    
    def setup_client_and_tracker(self):
        self.decode_torrent()
        self.tracker = Tracker(self)
        self.tracker.construct_tracker_url()
        self.tracker.send_request_and_parse_response()
        self.build_handshake()

    def send_and_receive_handshake(self, peer):
        peer.connect()
        print 'You have connected to your peer!'
        peer.sendall(self.handshake)
        print 'Sending handshake to peer...'
        peer_handshake = message.receive_data(peer, amount_expected=68, block_size=68)
        print 'Peer handshake has been received.'
        return peer_handshake

    def verify_handshake(self, handshake):
        # lenpstr - pstr - reserved - info hash - peer id
        (pstrlen, pstr, peer_hash, peer_id) = struct.unpack('B19s8x20s20s', handshake)
        return peer_hash == self.info_hash

    def add_peer(self, id, peer):
        self.peers[id] = peer
        
    def update_timeout(peer_id):
        pass

