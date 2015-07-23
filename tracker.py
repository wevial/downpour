import bencode as B
import requests
import urllib as U
import socket
import metainfo
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
            'peer_id': client.client_id,
            'port': '6881', 
            'left': client.file_length
        }
        self.full_url = self.construct_url(client.tracker_url)

    def construct_url(self, tracker_url):
        """ Construct the full URL for the torrent we're connecting to """ 
        params = '&'.join('%s=%s' % (key, U.quote(self.params[key])) 
                for key in self.params_order)
        full_url = self.tracker_url + '?' +  params
        return full_url

    def send_request_to_tracker(self):
        """ Returns bencoded request """
        return requests.get(url=self.full_url)

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

    def construct_peers(self, peer_tuples):
        peers = [Peer(ip, port) for ip, port in peer_tuples]
        for i, peer in enumerate(peers):
            self.client.add_peer(i, peer)

    def parse_response(self, response):
        response_text = B.bdecode(response.text)
        peer_ips = self.peers_to_ip_tuples(response_text['peers'])
        self.construct_peers(peer_ips)
