import os
import logging

class Stitcher:
    def __init__(self, client):
        self.num_pieces = client.num_pieces
        self.dload_dir = client.dload_dir
        self.is_multi_file = client.is_multi_file
        self.name = client.file_name
        self.path = os.path.join(self.dload_dir, 'torrtemp')
        self.write_file = open(self.path, 'ab')
        if self.is_multi_file:
            self.files = client.files
            self.create_main_dir()
            self.create_sub_directories()
#            self.create_multi_files()
            # Setup any directories needed for the files 
        else:
            self.path = os.path.join(self.dload_dir, self.name)
            self.main_dload_dir = self.dload_dir
        print 'main_dir:', self.main_dload_dir
        print 'dload_dir:', self.dload_dir

    def create_main_dir(self):
        self.main_dload_dir = os.path.join(self.dload_dir, self.name)
        try:
            os.makedirs(self.main_dload_dir)
        except OSError:
            if not os.path.isdir(self.main_dload_dir):
                raise SystemExit('Cannot create main directory [stitcher]')

    def create_sub_directories(self):
        logging.info('Creating sub directories')
        dir_paths = set()
        # set of directory paths
        for file_dict in self.files:
            if len(file_dict['path']) == 1:
                continue
            dir_path = self.main_dload_dir
            for dir_name in file_dict[:-1]:
                dir_path = os.path.join(dir_path, dir_name)
                if dir_path in directories:
                    try:
                        os.makedirs(dir_path)
                        dir_paths.add(dir_path)
                        logging.info('Created subdir %s', dir_path)
                    except OSError:
                        if not os.path.isdir(dir_path):
                            raise SystemExit('Cannot create necessary directories for torrent')

#    def create_multi_files(self):
#        """ Create a blank file for each file in a multiple file torrent. """
#        logging.info('Creating empty multi files')
#        for file_dict in self.files:
#            inner_path = '/'.join(file_dict['path'])
#            path = os.path.join(self.main_dload_dir, inner_path)
#            print path
#            write_file = open(path, 'wa')
#            file_dict['write_file'] = write_file
#            write_file.close()
#            logging.info('Created empty file @ %s', inner_path)
            
    def stitch(self):
        logging.info('Is multi file: %s', self.is_multi_file)
        logging.debug('Main_dload_dir %s', self.main_dload_dir)
        logging.debug('dload_dir %s', self.dload_dir)
        self.stitch_tmp_files()
        if self.is_multi_file:
            logging.debug('It is multi file stitching')
            self.stitch_multi_files()
        else:
            logging.debug('It is single file stitching')
            self.stitch_single_file()

    def stitch_tmp_files(self):
        """ Stitch temporary files into a single file. """
        logging.info('stitching tmp files')
        for i in range(self.num_pieces):
            piece_file_path = os.path.join(self.dload_dir, str(i))
            piece_file = open(piece_file_path, 'rb')
            self.write_file.write(piece_file.read())
            os.remove(piece_file_path)
        self.write_file.close()
        self.write_file = open(os.path.join(self.dload_dir, 'torrtemp'), 'rb')
    
    def stitch_single_file(self):
        logging.info('Renaming temp file to final, single file name')
        logging.info('PATH: %s, NAME: %s', self.dload_dir, self.path)
        os.rename(os.path.join(self.dload_dir, 'torrtemp'), self.path)

    def stitch_multi_files(self):
        logging.info('stitching Multi files')
        byte_count = 0
        for file_dict in self.files:
            logging.info('Writing %s', '/'.join(file_dict['path']))
            #, file_dict['write_file'])
            #write_file = open(file_dict['write_file'], 'ab')
            write_file = open(os.path.join(self.main_dload_dir, '/'.join(file_dict['path'])), 'ab')
            file_length = file_dict['length']
            self.write_file.seek(byte_count)
            write_file.write(self.write_file.read(file_length))
            byte_count += file_length
        os.remove(os.path.join(self.dload_dir, 'torrtemp'))
