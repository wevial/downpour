BLOCK_LENGTH = 2 ** 14
import random
import os
from mock import MagicMock

DIRNAME = '/tdownload/flag/'

class Piece(object):
    #Piece length is uniform across torrent (except last piece)
    #Number of blocks is uniform across torrent (except last piece)

    def __init__(self, index, length, piece_hash):
        self.length = length
        self.index = index 
        self.piece_hash = piece_hash
        self.rarity = 0
        self.peers = []
        self.num_blocks = self.length / BLOCK_LENGTH #Python 2 division!
        # print 'initialized piece: ', index, ' length ', length, ' # blocks ', self.num_blocks
        self.blocks_requested = 0
        self.blocks_received = 0
        curpath = os.path.abspath(os.curdir)
        #TODO: Change file implementation for multi-file torrents
        # self.write_file = open(os.path.join(curpath, 'tdownload', 
                        # 'flag', str(self.index)), 
                        # 'wb+')

    def __repr__(self):
        return str(self.index)

    def not_all_blocks_requested(self):
        return self.blocks_requested < self.num_blocks

    def add_peer_to_peer_list(self, peer):
        print 'peer ', peer, ' has piece ', self.index
        self.peers.append(peer)
        
    def get_block_to_send(self, begin, length):
        pass

    def write_block_to_file(self, begin, block):
        self.blocks_received += 1
        #Add if / else for last block situation!
        self.write_file.seek(begin)
        self.write_file.write(block)

    #Exposed method
    def get_next_block_and_peer_to_request(self):
        print 'getting block ', self.blocks_requested, ' of ', self.num_blocks
        begin = self.blocks_requested * BLOCK_LENGTH
        if self.blocks_requested == self.num_blocks - 1:
            length = self.length - self.blocks_requested * BLOCK_LENGTH
        else:
            length = BLOCK_LENGTH # This is another repetitive assignment
        self.blocks_requested += 1
        block_info = (self.index, begin, length)
        if len(self.peers):
            peer = random.choice(self.peers)
        else:
            peer = None
        return (block_info, peer) 
