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
from reactor import Reactor
from peer import Peer

TEST_TORRENT = 'flagfromserverorig.torrent'
BLOCK_LENGTH = 2 ** 14


class Client(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.reactor = Reactor()
        self.reactor_activated = False
        self.peer_id = '-TZ-0000-00000000000'
        self.peers = {}
        self.decode_torrent_and_setup_pieces()
        self.handshake = self.build_handshake()
        self.setup_tracker()
        self.setup_peers()

    def decode_torrent_and_setup_pieces(self):
        f = open(self.torrent, 'r')
        metainfo = B.bdecode(f.read())
        data = metainfo['info']  # Un-bencoded dictionary
        self.info_hash = H.sha1(B.bencode(data)).digest()
        self.file_length = data['length']
        self.piece_length = data['piece length']
        self.announce_url = metainfo['announce']
        self.file_name = data['name']
        self.setup_pieces(self.piece_length, data['pieces'])

    def setup_tracker(self):
        self.tracker = Tracker(self, self.announce_url)

    def setup_peers(self):
        peer_ips = self.tracker.send_request_and_parse_response()
        self.construct_peers(peer_ips)

    def construct_peers(self, peer_tuples):
        peers = [Peer(ip, port, self) for ip, port in peer_tuples]
        logging.info('Attempting to connect to peers %s', peer_tuples)
        for i, peer in enumerate(peers):
            try:
                peer.connect()
                peer_handshake = peer.send_and_receive_handshake(self.handshake)
            except IOError:
                logging.info('Error connecting to peer %s', peer)
            else:
                if peer.verify(peer_handshake, self.handshake):
                    self.add_peer(i, peer)
                    if not self.reactor_activated:
                        self.activate_reactor()

    def activate_reactor(self):
        logging.info('activating reactor')
        self.reactor.get_data()

    def build_handshake(self):
        logging.info('Building handshake')
        pstr = 'BitTorrent protocol'
        handshake = struct.pack('B' + str(len(pstr)) + 's8x20s20s',
                                # 8x => reserved null bytes
                                len(pstr),
                                pstr,
                                self.info_hash,
                                self.peer_id
                                )
        assert len(handshake) == 49 + len(pstr)
        return handshake

    def add_peer(self, id_num, peer):
        logging.info('adding peer %s to peer list', peer)
        self.peers[id_num] = peer
        self.reactor.add_peer_socket(peer)

    def update_timeout(self, peer_id):
        pass

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

    def setup_pieces(self, length, hash_bytes):
        hash_list = self.process_raw_hash_list(hash_bytes, 20)
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

    # TODO implement real strategies :)
    def start_pieces_in_order_strategy(self):
        for piece_id, do_i_have in enumerate(self.bitfield):
            if not do_i_have:
                # TODO fix formatting here, it's ugly
                piece = self.pieces[piece_id]
                logging.info('getting piece %s', piece)
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
