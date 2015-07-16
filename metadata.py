import bencode as B

class Metadata:
    def __init__(self):
#        self.torrent = 'Defiance.S03E06.HDTV.x264-ASAP.mp4[eztv].torrent'
        self.torrent = 'flagfromserverorig.torrent'

    def decode(self):
        f = open(self.torrent, 'r')
        metadata = f.read()
        metadata = B.bdecode(metadata)
        self.data = metadata
#        return metadata
