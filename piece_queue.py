import random
import logging

class PieceQueue(object):
    def __init__(self, pieces):
        self.pieces = pieces[:]
        self.state = 'random'
        self.pieces_requested = 0

    def empty(self):
        return len(self.pieces) == 0

    def length(self):
        return len(self.pieces)

    def put(self, piece):
        self.pieces.insert(0, piece)

    def update_state(self, state):
        self.state = state

    def update_piece_order(self):
        self.pieces.sort()

    # TODO: Refactor to use polymorphism?
    def get_next_piece(self, torrent_state):
        if not self.empty():
            if torrent_state == 'random':
                piece = self.get_next_random()
            elif torrent_state == 'rarest_first':
                piece = self.get_next_rarest_first()
            self.pieces_requested += 1
            return piece
        else:
            return False

    def get_next_random(self):
        return self.pieces.pop(random.randint(0, len(self.pieces) - 1))

    def get_next_rarest_first(self, chunk_size = 5):
        # Gets next piece at random from the (five) rarest pieces remaining 
        if len(self.pieces) > chunk_size: 
            logging.warning('Last chunk of pieces should be requsted at random')
        next_index = random.randint(max(0, len(self.pieces) - chunk_size), len(self.pieces) - 1)
        logging.info('Geetting piece %s off piece queue length %s', next_index, len(self.pieces))
        return self.pieces.pop(next_index)

