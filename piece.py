BLOCK_LENGTH = 2 ** 14
import fs

DIRNAME = '/tdownload/flag/'

class Piece(object):
    #Piece length is uniform across torrent (except last piece)
    #Number of blocks is uniform across torrent (except last piece)

    def __init__(self, index, length, info_hash):
        self.length = length
        self.index = index 
        self.info_hash = info_hash
        self.rarity = 0
        self.peers = []
        self.blocks_requested = 0
        self.blocks_received = 0
        self.file_name = open(DIRNAME + self.index, 'wb') # TODO: IMPLEMENT DIR

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
