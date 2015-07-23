import bencode as B

class Metainfo:
    def __init__(self):
        self.torrent = 'flagfromserverorig.torrent'

    def decode_torrent(self, torrent):
        f = open(torrent, 'r')
        metainfo = f.read()
        decoded_info = B.bdecode(f.read())
        self.data = metainfo # Un-bencoded dictionary
