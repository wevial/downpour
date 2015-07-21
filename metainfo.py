import bencode as B

class Metainfo:
    def __init__(self):
        self.torrent = 'flagfromserverorig.torrent'

    def decode(self):
        f = open(self.torrent, 'r')
        metainfo = f.read()
        metainfo = B.bdecode(metainfo)
        self.data = metainfo # Un-Bencoded dictionary
