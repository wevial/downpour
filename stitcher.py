import os

class Stitcher:
    def __init__(self, file_name, num_pieces):
        self.file_name = file_name
        self.path = os.path.abspath(os.curdir)
        self.num_pieces = num_pieces
        self.write_file = open(os.path.join(self.path, 'tdownload',
                               'flag', file_name), 'ab')

    def stitch_files(self):
        for i in range(self.num_pieces):
            piece_file = open(os.path.join(self.path, 'tdownload',
                              'flag', str(i)), 'rb')
            self.write_file.write(piece_file.read())
