import hashlib as H
import bencode as B
import struct
from bitstring import BitArray
from textwrap import wrap

from tracker import Tracker
import peer
import message
import pieces

TEST_TORRENT = 'flagfromserverorig.torrent'

class Client(object):
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
        pieces.Piece.set_piece_length(self.piece_length)
        self.piece_hashes = wrap(metainfo_data['pieces'], 20)
        peer.Peer.num_pieces = len(self.piece_hashes)
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

    def add_peer(self, id_num, peer):
        self.peers[id_num] = peer
    
    def update_timeout(peer_id):
        pass

