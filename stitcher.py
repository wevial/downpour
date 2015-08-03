import os

class Stitcher:
    def __init__(self, file_name, num_pieces, dload_dir, is_multi_file=False):
        self.file_name = file_name
        self.path = os.path.abspath(os.curdir)
        self.num_pieces = num_pieces
        self.dload_dir = dload_dir
        self.write_file = open(os.path.join(dload_dir, file_name), 'ab')
        self.is_multi_file = is_multi_file

    def stitch_tmp_files(self):
        for i in range(self.num_pieces):
            piece_file_path = os.path.join(self.dload_dir, str(i))
            piece_file = open(piece_file_path, 'rb')
            self.write_file.write(piece_file.read())
            os.remove(piece_file_path)

    def stitch_multi_files(self):
        stitch_all_files()
        # TODO: split write file into multiple files
        pass
