import hashlib as H
import bencode as B
import struct
from bitstring import BitArray
from textwrap import wrap

from tracker import Tracker
import message

TEST_TORRENT = 'flagfromserverorig.torrent'

class Client(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_id = '-TZ-0000-00000000000'
        self.peers = {}
        self.setup_client_and_tracker()

    def decode_torrent(self):
        f = open(self.torrent, 'r')
        metainfo = B.bdecode(f.read())
        self.announce_url = metainfo['announce']
        metainfo_data = metainfo['info'] # Un-bencoded dictionary
        self.info_hash = H.sha1(B.bencode(metainfo_data)).digest()
        self.piece_length = metainfo_data['piece length']
        self.piece_hashes = wrap(metainfo_data['pieces'], 20)
        self.num_pieces = len(self.piece_hashes) # Total number of pieces
        self.bitfield = BitArray(self.num_pieces)
        self.file_name = metainfo_data['name']
        self.left = metainfo_data['length']

    def setup_piece_info_peers(self):
        self.piece_info_peers = [[] for _ in range(self.num_pieces)]

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
        self.setup_piece_info_peers()

    def add_peer(self, id_num, peer):
        self.peers[id_num] = peer
    
    def update_timeout(self, peer_id):
        pass

    def select_request(self):
        pass

    def update_piece_peer_list(self, piece_index, peer):
        self.piece_info_peers[piece_index].append(peer)
        self.pretty_print_piece_peer_list()

    def get_block(self, block_info):
        pass

    def update_block_info(self, block_info):
        pass

    def write_block_to_file(self, block_info, block):
        pass

    ##### HELPER FUNCTIONS #####
    def pretty_print_piece_peer_list(self):
        s = ''
        for i in self.piece_info_peers:
            s += '1' if len(i) > 0 else '0'
        print s
