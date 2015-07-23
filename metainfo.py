import bencode as B
import textwrap

class Metainfo:
    def __init__(self):
        self.torrent = 'flagfromserverorig.torrent'

    def decode(self):
        f = open(self.torrent, 'r')
        metainfo = f.read()
        metainfo = B.bdecode(metainfo)
        self.data = metainfo # Un-bencoded dictionary

    def seperate_pieces(self):
        self.piece_hashes = textwrap.wrap(self.data['info']['pieces'])


