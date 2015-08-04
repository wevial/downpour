import hashlib as H
import bencode as B
import struct
import logging
import message
import os, sys
from bitstring import BitArray
from tracker import Tracker
from piece import Piece
from stitcher import Stitcher

logging.basicConfig(filename='example.log', filemode='w', level=logging.INFO)

TEST_TORRENT = 'flagfromserverorig.torrent'
BLOCK_LENGTH = 2 ** 14


class Client(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_id = '-TZ-0000-00000000000'
        self.peers = {}
        self.setup_client_and_tracker()

    def process_raw_hash_list(self, hash_list, size):
        tmp_hash = ''
        piece_hashes = []
        for char in hash_list:
            if len(tmp_hash) < size:
                tmp_hash = tmp_hash + char
            else:
                piece_hashes.append(tmp_hash)
                tmp_hash = char
        piece_hashes.append(tmp_hash)
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
        self.setup_download_directory()
        self.check_if_dload_file_exists()
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
            pieces.append(Piece(i, length, hash_list[i], self.dload_dir))
        self.pieces = pieces

    def setup_download_directory(self):
        dir_name = self.torrent
        if dir_name.endswith('.torrent'):
            dir_name = dir_name[:-8]
        self.dload_dir = os.path.join(os.path.abspath(os.curdir), dir_name)
        try:
            os.makedirs(self.dload_dir)
        except OSError:
            if not os.path.isdir(self.dload_dir):
                raise SystemExit('Cannot create directory to download torrent files into. Please check if a file named ' + dir_name + ' exists') 
#                raise OSError('Cannot create directory to download torrent files to.')

    def check_if_dload_file_exists(self):
        file_path = os.path.join(self.dload_dir, self.file_name)
        if os.path.exists(file_path):
            raise SystemExit('The file you are trying to download already exists.')
            # Do something to cancel the rest of the setup

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
        logging.info('Got block to write from piece %s', piece_index)
        piece = self.pieces[piece_index]
        piece.write_block_to_file(begin, block)
        self.tracker.update_download_stats(block_length)
        if piece_index == self.num_pieces - 1:
            # FINALIZE IS ONLY TEMPORARILY HERE!!! Naive strategy only
            self.finalize_download()
    
    def finalize_download(self):
        logging.info('Finalizing download')
        assert self.tracker.is_download_complete()
        self.stitch_files()
        # Graceful shutdown 
        for peer in self.peers.itervalues():
            print 'hi'
        sys.exit()

    def stitch_files(self):
        logging.info('Wrote all pieces, stitching them together')
        stitcher = Stitcher(self.file_name, self.num_pieces, self.dload_dir)
        stitcher.stitch_tmp_files()
        logging.info('Stitching completed.')
