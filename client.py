import hashlib as H
import bencode as B
import struct
from bitstring import BitArray
import logging

logging.basicConfig(filename='example.log', filemode='w', level=logging.INFO)

from tracker import Tracker
from piece import Piece
import message
from stitcher import Stitcher

TEST_TORRENT = 'flagfromserverorig.torrent'
BLOCK_LENGTH = 2 ** 14


class Client(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_id = '-TZ-0000-00000000000'
        self.peers = {}
        self.setup_client_and_tracker()

    def process_raw_hash_list(self, hash_list, size):
        tmp = ''
        piece_hashes = []
        for char in hash_list:
            if len(tmp) < size:
                tmp = tmp + char
            else:
                piece_hashes.append(tmp)
                tmp = char
        piece_hashes.append(tmp)
        return piece_hashes

    def decode_torrent_and_start_setup(self):
        f = open(self.torrent, 'r')
        metainfo = B.bdecode(f.read())
        data = metainfo['info']  # Un-bencoded dictionary
        # Client
        self.info_hash = H.sha1(B.bencode(data)).digest()
        self.file_length = data['length']

        # Tracker
        self.announce_url = metainfo['announce']

        # Pieces
        self.file_name = data['name']
        self.setup_pieces(data['piece length'],
                          self.process_raw_hash_list(data['pieces'], 20))

    def setup_pieces(self, length, hash_list):
        logging.info('setting up pieces for file length, %s',  length)
        pieces = []
        self.num_pieces = len(hash_list)
        # assert self.num_pieces == self.raw_hashes / 20
        # Raw hashes is always multiple of 20
        logging.info('dividing up file into %s pieces', self.num_pieces)
        self.bitfield = BitArray(self.num_pieces)
        last_piece_length = self.file_length - (self.num_pieces - 1) * length
        for i in range(self.num_pieces):
            if i == self.num_pieces - 1:
                logging.info('Setting up last piece, length: %s', last_piece_length)
                length = last_piece_length
            pieces.append(Piece(i, length, hash_list[i]))
        self.pieces = pieces


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
        self.decode_torrent_and_start_setup()
        self.tracker = Tracker(self)
        self.tracker.construct_tracker_url()
        self.tracker.send_request_and_parse_response()
        self.build_handshake()

    def add_peer(self, id_num, peer):
        self.peers[id_num] = peer

    def update_timeout(self, peer_id):
        pass

    # TODO implement real strategies :)
    def start_pieces_in_order_strategy(self):
        for piece_id, do_i_have in enumerate(self.bitfield):
            if not do_i_have:
                # TODO fix formatting here, it's ugly
                piece = self.pieces[piece_id]
                logging.info('getting piece %s', piece)
                # TODO: Make this loop work
                while piece.not_all_blocks_requested():
                    block_i_want, peer = piece.get_next_block_and_peer_to_request()
                    block_message = message.RequestMsg(block_i_want)
                    logging.info('queueing up message for block %s', block_i_want)
                    if peer:
                        peer.add_to_message_queue(block_message)
                    else:
                        logging.warning('Why is there a piece with no blocks?')

    def select_request_random(self):
        pass

    def add_peer_to_piece_peer_list(self, piece_index, peer):
        print 'adding piece ', piece_index, 'to peer', peer
        self.pieces[piece_index].add_peer_to_peer_list(peer)

    def get_next_block(self, piece_index):
        self.pieces[piece_index].get_next_block_and_peer_to_request()

    def write_block_to_file(self, block_info, block):
        (piece_index, begin, block_length) = block_info
        logging.info('got block from piece %s', piece_index)
        piece = self.pieces[piece_index]
        piece.write_block_to_file(begin, block)
        if piece_index == self.num_pieces - 1:
            logging.info('Wrote all pieces, stitching them together')
            stitcher = Stitcher(self.file_name, self.num_pieces)
            stitcher.stitch_files()
            logging.info('stitching complete')

    # HELPER FUNCTIONS
    def pretty_print_piece_peer_list(self):
        s = ''
        for i in self.piece_info_peers:
            s += '1' if len(i) > 0 else '0'
        print s
