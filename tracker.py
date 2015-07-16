import bencode as B
import hashlib as H
import requests
#import util

class Tracker:
    def __init__(self, metadata):
        self.torrent = metadata.torrent
        self.tracker_url = metadata.data['announce']
        self.params = {
            'uploaded': '0',
            'compact': '1',
            'info_hash': H.sha1(B.bencode(metadata.data['info'])).digest(),
            'event': 'started',
            'downloaded': '0',
            'peer_id': '-TZ-0000-00000000000',
            'port': '6881', 
            'left': str(metadata.data['info']['length']),
        }

    def send_request(self):
        print self.params
        return requests.get(url=self.tracker_url, params=self.params)
