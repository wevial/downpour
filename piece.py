BLOCK_LENGTH = 2 ** 14
import fs

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
        self.blocks_requested = 0
        self.blocks_received = 0
        self.file_name = open(DIRNAME + self.index, 'wb') # TODO: IMPLEMENT DIR

    def add_peer_to_peer_list(self, peer):
        self.peers.append(peer)

    def get_block_to_send(self, begin, length):
        pass

    def write_block_to_file(self, begin, block):
        self.file_name.seek(begin)
        self.file_name.write(block)

    def get_next_block_info(self):
        begin = self.blocks_requested * BLOCK_LENGTH
        if self.blocks_requested == self.num_blocks - 1:
            length = self.length - self.blocks_requested * BLOCK_LENGTH
        else:
            length = BLOCK_LENGTH # This is another repetitive assignment
        self.blocks_requested += 1
        return (self.piece_index, begin, length) 
