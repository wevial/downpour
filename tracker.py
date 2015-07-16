import bencode as B
import hashlib as H
import requests
import urllib as U
#import util
#url_encode the info_hash

class Tracker:
    def __init__(self, metadata):
        self.torrent = metadata.torrent
        self.tracker_url = metadata.data['announce']
        self.params_order = ['uploaded', 'compact', 'info_hash', 'event', 
                'downloaded', 'peer_id', 'port', 'left']
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
    def construct_url(self):
        params = '&'.join('%s=%s' % (key, U.quote(self.params[key])) for key in self.params_order)
        full_url = self.tracker_url + '?' +  params
        self.full_url = full_url

    def send_request(self):
        return requests.get(url=self.full_url)
