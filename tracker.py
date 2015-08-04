import bencode as B
import requests
import urllib as U
from peer import Peer

class Tracker:
    def __init__(self, client):
        self.client = client
        self.params_order = ['uploaded', 'compact', 'info_hash', 'event', 
                'downloaded', 'peer_id', 'port', 'left']
        self.params = {
            'uploaded': '0',
            'compact': '1',
            'info_hash': client.info_hash,
            'event': 'started',
            'downloaded': '0',
            'peer_id': client.peer_id,
            'port': '6881', 
            'left': str(client.file_length),
        }
        self.file_length = client.file_length
#        self.url = self.construct_url(client.announce_url)

    def is_download_complete(self):
        if self.params['event'] == 'completed':
            return True
        elif int(self.params['downloded']) == self.file_length:
            logging.info('Tracker has marked download as completed')
            assert int(self.params['left']) == 0
            self.params['event'] = 'completed'
            return True
        logging.debug('Tracker says download has not completed')
        return False
                
    def update_download_stats(self, num_bytes_dloaded):
        downloaded = int(self.params['downloaded']) + num_bytes_dloaded
        left = int(self.params['left']) - num_bytes_dloaded
        self.params['downloaded'] = str(downloaded) 
        self.params['left'] = str(left)
        logging.info('%s bytes downloaded (%s%)', downloaded, (downloaded/self.file_length))
        logging.info('%s bytes left to download', left)

    def construct_tracker_url(self):
        """ Construct the full URL for the torrent we're connecting to """ 
        #print self.params
        params = '&'.join('%s=%s' % (key, U.quote(self.params[key])) 
                for key in self.params_order)
        tracker_url = self.client.announce_url + '?' +  params
        self.url = tracker_url
        return tracker_url

    def send_request_to_tracker_server(self):
        """ Returns bencoded handshake request """
        print "Request sent to tracker server."
        return requests.get(url=self.url)

    def peer_host_port_vals(self, peers):
        #Get values of all bytes in byte_string list of peers
        peer_host_port_values = []
        while len(peers) > 0:
            peer_host_port_values.append( [ ord(peer) for peer in peers[0:6] ] )
            peers = peers[6:]
        return peer_host_port_values

    def get_host_string(self, peer_byte_list):
        return '.'.join([str(val) for val in peer_byte_list[0:4]])

    def get_port(self, peer_byte_list):
        return 256 * peer_byte_list[4] + peer_byte_list[5]

    def peers_to_ip_tuples(self, peer_bytes):
        byte_list = self.peer_host_port_vals(peer_bytes)
        return [(self.get_host_string(peer), self.get_port(peer)) for peer in byte_list]

    def construct_peers_for_client(self, peer_tuples):
        peers = [Peer(ip, port, self.client) for ip, port in peer_tuples]
        for i, peer in enumerate(peers):
            self.client.add_peer(i, peer)

    def parse_response(self, response):
        response_text = B.bdecode(response.text)
        peer_ips = self.peers_to_ip_tuples(response_text['peers'])
        self.construct_peers_for_client(peer_ips)
        print 'Tracker response parsed.'
        
    def send_request_and_parse_response(self):
        response = self.send_request_to_tracker_server()
        self.parse_response(response)

