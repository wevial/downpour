import hashlib as H
import random
import os
import logging

BLOCK_LENGTH = 2 ** 14


class Piece(object):
    #Piece length is uniform across torrent (except last piece)
    #Number of blocks is uniform across torrent (except last piece)
    #TODO: Change file implementation so that piece initialization passes file info?

    def __init__(self, index, length, piece_hash, dload_dir):
        self.length = length
        self.index = index
        self.piece_hash = piece_hash
        self.rarity = 0
        self.peers = []
        self.num_blocks = self.length / BLOCK_LENGTH # Python 2 division!
        # print 'initialized piece: ', index, ' length ', length, ' # blocks ', self.num_blocks
        self.blocks_requested = 0
        self.blocks_received = 0
        self.dload_dir = dload_dir
        self.create_write_file()

        #TODO: Separate out temp file creation from file writing

    def create_write_file(self):
        file_path = os.path.join(self.dload_dir, str(self.index))
        open(file_path, 'wa').close() # Create file if it does not exist
        self.write_file = open(file_path, 'r+b')

    def __repr__(self):
        return str(self.index)

    def not_all_blocks_requested(self):
        return self.blocks_requested <= self.num_blocks

    def add_peer_to_peer_list(self, peer):
        print 'peer ', peer, ' has piece ', self.index
        self.peers.append(peer)

    def check_info_hash(self):
        self.write_file.seek(0)
        file_bytes = self.write_file.read()
        computed_hash = H.sha1(file_bytes).digest()
        return computed_hash == self.piece_hash

    def save_or_delete(self):
        if self.check_info_hash():
            logging.debug('Awesome, info hash is correct')
            # self.client.add_piece_to_bitfield(self.index)
        else:
            logging.warning('Incorrect info hash for piece %s', self.index)
            self.reset()

    def reset(self):
        self.blocks_received = 0
        self.blocks_requested = 0
        self.create_write_file()
        # TODO: UPDATE CLIENT

    def check_if_finished(self):
        return self.blocks_received == self.num_blocks

    def update_block_count(self):
        self.blocks_received += 1

    def write_block_to_file(self, begin, block):
        print 'Writing to piece', self.index, 'at position', begin
        self.write_file.seek(begin)
        self.write_file.write(block)

    # TODO: Fix interface after block message to use add block
    def add_block(self, begin, block):
        self.update_block_count()
        self.write_block_to_file(begin, block)
        if self.check_if_finished():
            self.save_or_delete()

    # Exposed method
    def get_next_block_and_peer_to_request(self):
        print 'Getting block ', self.blocks_requested, ' of ', self.num_blocks
        begin = self.blocks_requested * BLOCK_LENGTH
        if self.blocks_requested == self.num_blocks:
            length = self.length - self.blocks_requested * BLOCK_LENGTH
            logging.info('Calculating length of last block: %s', length)
        else:
            length = BLOCK_LENGTH # This is another repetitive assignment
        self.blocks_requested += 1
        block_info = (self.index, begin, length)
        if len(self.peers):
            peer = random.choice(self.peers)
        else:
            # TODO: Setup some sort of error here?
            peer = None
        return (block_info, peer)
