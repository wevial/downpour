import hashlib as H
import bencode as B
import struct
import logging
import random

logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)

import socket
import message
import os, sys
from bitstring import BitArray
from tracker import Tracker
from piece import Piece

from stitcher import Stitcher
from reactor import Reactor
from peer import Peer
from piece_queue import PieceQueue

TEST_TORRENT = 'flagfromserverorig.torrent'
BLOCK_LENGTH = 2 ** 14
PIECE_THRESHOLD = 5


class Client(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.torrent_state = 'random'
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
        self.setup_download_directory()
        self.check_if_dload_file_exists()
        self.setup_pieces(self.piece_length, data['pieces'])

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
        assert handshake != None
        assert len(handshake) == 49 + len(pstr)
        logging.info('Handshake constructed.')
        return handshake

    def setup_tracker(self):
        self.tracker = Tracker(self, self.announce_url)

    def setup_peers(self):
        peer_ips = self.tracker.send_request_and_parse_response()
        self.connect_to_peers(peer_ips)

    def connect_to_peers(self, peer_tuples):
        peers = [Peer(ip, port, self) for ip, port in peer_tuples]
        logging.debug('Attempting to connect to peers %s', peer_tuples)
        for i, peer in enumerate(peers):
            try:
                if peer.ip == self.get_self_ip():
                    logging.info('Skipping peer; cannot connect to self')
                    continue
                peer.connect()
                peer_handshake = peer.send_and_receive_handshake(self.handshake)
                logging.debug('Handshake returned.')
                if peer.verify_handshake(peer_handshake, self.info_hash):
                    logging.debug('Handshake verified. Adding peer to peer list')
                    self.add_peer(i, peer)
                    if not self.reactor_activated:
                        self.activate_reactor()
                        self.reactor_activated = True
                        logging.info('About to start piece requesting')
            except IOError as e:
                logging.warning('%s', e)
        self.manage_requests(5)
            # except Exception as e:
                # logging.debug('Error %s connecting to peer %s. [In construct_peers]', e, peer)

    def get_self_ip(self):
        # http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/166520#166520
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def add_peer(self, id_num, peer):
        logging.info('adding peer %s to peer list', peer)
        self.peers[id_num] = peer
        self.reactor.add_peer_socket(peer)

    def activate_reactor(self):
        logging.debug('Activating reactor.')
        self.reactor.get_data()

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

    def setup_pieces(self, length, hash_bytes):
        hash_list = self.process_raw_hash_list(hash_bytes, 20)
        logging.info('setting up pieces for file length, %s',  length)
        pieces = []
        self.num_pieces = len(hash_list)
        logging.info('dividing up file into %s pieces', self.num_pieces)
        self.bitfield = BitArray(self.num_pieces)
        last_piece_length = self.file_length - (self.num_pieces - 1) * length
        for i in range(self.num_pieces):
            if i == self.num_pieces - 1:
                length = last_piece_length
            pieces.append(Piece(self, i, length, hash_list[i], self.dload_dir))
            logging.info('Created piece index %s length %s', i, length)
        self.pieces = pieces
        self.piece_queue = PieceQueue(pieces)
        logging.info('Created piece queue length %s', len(self.piece_queue.pieces))

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
                # raise OSError('Cannot create directory to download torrent files to.')

    def check_if_dload_file_exists(self):
        file_path = os.path.join(self.dload_dir, self.file_name)
        if os.path.exists(file_path):
            raise SystemExit('This file has already been downloaded.')
            # Do something to cancel the rest of the setup

    def add_piece_to_queue(self, piece):
        self.piece_queue.put(piece)

    def add_piece_to_bitfield(self, index):
        if not self.bitfield[index]:
            self.bitfield.invert(index)
            self.manage_requests()
        else:
            logging.warning('Should never get save same piece more than once!')

    def add_peer_to_piece_peer_list(self, piece_index, peer):
        print 'Adding piece', piece_index, 'to peer', peer
        self.pieces[piece_index].add_peer_to_peer_list(peer)

    def manage_requests(self, num_pieces=1):
        logging.info('Sending more piece requests')
        logging.info('Piece queue has %s pieces', self.piece_queue.length())
        if not self.piece_queue.empty():
            self.manage_piece_queue_state();
            for i in xrange(num_pieces):
                self.request_next_piece();
            logging.info('Cleaning up piece queue')
        else:
            pass

    def manage_piece_queue_state(self):
        # This should probably only get called occasionally
        logging.debug('Have received %s pieces, need %s more', self.bitfield.count(1), self.bitfield.count(0))
        if self.bitfield.count(1) > PIECE_THRESHOLD and self.piece_queue.length() > PIECE_THRESHOLD:
            self.piece_queue.update_piece_order()
            self.piece_queue.update_state('rarest_first')
        elif self.piece_queue.length() <= PIECE_THRESHOLD:
            logging.info('Switching to random state')
            self.piece_queue.update_state('random')
        self.request_next_piece()

    # DISPATCHES TO PIECE
    def request_next_piece(self):
        next_piece = self.piece_queue.get_next_piece()
        logging.info('Requesting piece %s', next_piece)
        if next_piece:
            try:
                next_piece.request_all_blocks()
            except IndexError as e:
                self.piece_queue.put(next_piece)
                logging.error(e)

    def write_block_to_file(self, block_info, block):
        (piece_index, begin, block_length) = block_info
        logging.info('Writing block of length %s at index %s for piece %',
                block_length, begin, piece_index)
        piece = self.pieces[piece_index]
        logging.info('Piece has index %s', piece.index)
        piece.add_block(begin, block)
        self.tracker.update_download_stats(block_length)
        if self.num_pieces - self.bitfield.count(1) == 0:
            self.finalize_download()
    
    def finalize_download(self):
        logging.info('Finalizing download')
        # assert self.tracker.is_download_complete()
        self.stitch_files()
        # Graceful shutdown 
        logging.info('Shutting down connection with peers')
        for peer in self.peers.itervalues():
            peer.close()
        print 'Quitting client'
        logging.info('Download completed. Quitting client.')
        sys.exit()

    def stitch_files(self):
        logging.info('Wrote all pieces, stitching them together')
        stitcher = Stitcher(self.file_name, self.num_pieces, self.dload_dir)
        stitcher.stitch_tmp_files()
        logging.info('Stitching completed.')
