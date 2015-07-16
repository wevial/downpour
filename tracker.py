import bencode as B
import requests as R
import hashlib as H

class Tracker:
    def __init__(self):
        self.torrent = 'flagfromserverorig.torrent' #if torrent == None else torrent

    def decode(self):
        f = open(self.torrent, 'r')
        metadata = f.read()
        metadata = B.bdecode(metadata)
        self.metadata = metadata
        return metadata

    def send_request(self):
        if not hasattr(self, metadata):
            self.decode()
        tracker_url = self.metadata['announce']
        info_hash = H.sha1(B.encode(self.metadata['info']))


