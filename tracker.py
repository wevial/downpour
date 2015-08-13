import bencode as B
import requests
import urllib as U
import logging
import socket
import random
import struct


class Tracker:
    def __init__(self, client, announce_urls):
        logging.info('setting up tracker')
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
        self.connection_id = 0x41727101980
        self.file_length = client.file_length
        # new
        self.announce(announce_urls)
        # old
        # self.announce_url = announce_url
        # self.url = self.construct_tracker_url(announce_url)

    #### GENERAL METHODS ####
    def announce(self, announce_urls):
        for url in announce_urls:
            print url
        print '\n'

        announce_urls = set(announce_urls)
        for announce_url in announce_urls:
            if is_udp_url(announce_url):
                self.is_udp = True
                self.open_udp_socket()
                is_connected = self.connect_to_tracker_udp(announce_url)
                if is_connected:
                    valid_announce = self.udp_announce()
                    if valid_announce:
                        return self.peers
                self.socket.close()
            else:
                self.is_udp = False
                self.tracker_url = self.construct_tracker_url(announce_url)
                self.send_request_and_parse_response()
                return self.peers
        logging.info('exiting for loop')
    
    def parse_announce_url(self, announce_url):
        """ Get host url and port from announce_url """
        announce_url = announce_url.rstrip('/announce')
        host_index = announce_url.rfind('/') + 1
        port_index = announce_url.rfind(':')
        host = announce_url[host_index:port_index]
        port = int(announce_url[port_index + 1:])
        print announce_url
        return (host, port)

    def is_download_complete(self):
        if int(self.params['downloaded']) == self.file_length:
            logging.info('Tracker has marked download as completed')
            logging.debug('Left to dload: %s', self.params['left'])
            self.params['event'] = 'completed'
        return self.params['event'] == 'completed'

    def send_completed_msg_to_tracker_server(self):
        logging.info('Tell the tracker server that the download has completed')
        # tracker_url = self.construct_tracker_url(self.announce_url)
        requests.get(url=self.tracker_url)
        logging.info('Tracker response to completed download: %s')
                
    def update_download_stats(self, num_bytes_dloaded):
        downloaded = int(self.params['downloaded']) + num_bytes_dloaded
        left = int(self.params['left']) - num_bytes_dloaded
        self.params['downloaded'] = str(downloaded) 
        self.params['left'] = str(left)
        percent_dloaded = int(float(downloaded) / float(self.file_length) * 100.0)
        logging.info('%s bytes downloaded (%s / 100)', downloaded, percent_dloaded)
        logging.info('%s bytes left to download', left)

    #### UDP METHODS ####
    def udp_announce(self):
        logging.info('Announcing to tracker %s', self.host_port)
        announce_packet = self.create_udp_announce_packet()
        response = self.send_packet(announce_packet)
        action_sent = 1
        valid_response = self.check_udp_response(action_sent, response)
        if valid_response:
            logging.info('Announce with %s successful', self.host_port)
        else:
            logging.info('Announce with %s unsuccessful', self.host_port)
        return valid_response

    def get_udp_peers(self, response):
        logging.info('Getting peers!')
        if len(response) < 6: 
            raise SystemExit('Oops faulty response')
        interval, num_leechers, num_seeders = struct.unpack('!3i', response[:12])
        logging.info('Total number of peers: %s', (num_seeders + num_leechers))
        logging.info('Seeders: %s, Leechers: %s', num_seeders, num_leechers)
        peers_to_unpack = response[12:]
        peers = []
        # Try with just number of seeders rather than total peers if doesnt work?
        count = 0
        while peers_to_unpack and count < 50:
            peer = peers_to_unpack[:6]
            peers_to_unpack = peers_to_unpack[6:]
            peers.append(self.unpack_udp_peer(peer))
            count += 1
        logging.info('Number of peers extracted: %s', len(peers))
#        logging.info('List of peers: %s', peers)
        return peers

    def unpack_udp_peer(self, peer):
        ip, port = struct.unpack('!iH', peer)
        ip = socket.inet_ntoa(struct.pack('!i', ip))
        return (ip, int(port))

    def connect_to_tracker_udp(self, announce_url):
        (host, port) = self.parse_announce_url(announce_url)
        self.announce_url = announce_url
        self.host_port = (host, port)
        action_sent = 0
        logging.info('Attempting to connect to %s', self.host_port)
        connect_packet = self.create_udp_packet_prefix(action_sent)
        try:
            response = self.send_packet(connect_packet)
            valid_response = self.check_udp_response(action_sent, response)
            if valid_response:
                logging.info('Connecting to tracker %s was successful!', host)
            else:
                logging.info('No connection to %s. Invalid response from host', host)
            return valid_response 
        except socket.timeout:
            logging.info('Could not connect to tracker %s :(', host)
            return False
            
    def open_udp_socket(self):
        logging.info('Opening UDP socket')
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(15) # standard timeout is 15 sec
            logging.info('UDP socket opened with timeout')
        except socket.error:
            logging.warning('Could not create UDP socket for tracker.')
            raise SystemExit ('Could not create UDP socket for tracker.')

    def check_udp_response(self, action_sent, response):
        if response == None:
            return False
        action_recv = struct.unpack('!i', response[:4])[0]
        transaction_id_recv = struct.unpack('!i', response[4:8])[0]
        if action_recv != action_sent:
            logging.warning('Action received (%s) does not match action sent (%s)',
                    action_recv, action_sent)
            return False
            # Attempt next announce URL
        elif transaction_id_recv != self.transaction_id:
            logging.warning('Transaction id received (%s) does not match id sent (%s)',
                    transaction_id_recv, self.transaction_id)
            return False
            # Also attempt next announce URL. Can collapse into both into single stmt
        self.parse_udp_response(action_sent, response)
        return True

    def parse_udp_response(self, action, response):
        if action == 0:
            logging.info('Connect packet received. Changing connection_id')
            self.connection_id = struct.unpack('!q', response[8:])[0]
            logging.info('New connection_id: %s', self.connection_id)
        elif action == 1:
            logging.info('Announce packet received. Go on to get peers!')
            self.peers = self.get_udp_peers(response[8:])
        else:
            # Only exitting for the time being...
            raise SystemExit('Action ' + str(action) + 'not supported')
    
    def create_udp_packet_prefix(self, action):
        self.transaction_id = random_32_bit_int()
        return struct.pack('!q2i',
                self.connection_id,
                action,
                self.transaction_id
                )

    def create_udp_announce_packet(self):
        logging.info('Creating announce packet for %s', self.host_port)
        prefix = self.create_udp_packet_prefix(action=1)
        return prefix + struct.pack('!20s20s3qi2IiH',
                self.params['info_hash'],
                self.params['peer_id'],
                int(self.params['downloaded']),
                int(self.params['left']),
                int(self.params['uploaded']),
                self.get_event_id(),
                0, # default (auto) ip address
                random_32_bit_int(), # unique random key
                -1, # default max num of peers
                int(self.params['port']),
                ) 

    def get_event_id(self):
        event = self.params['event']
        if event == 'completed':
            return 1
        elif event == 'started':
            return 2
        else: #event == 'stopped'
            return 3

    def send_packet(self, packet):
        host, port = self.host_port
        print self.host_port
        print repr(packet)
        try:
            self.socket.sendto(packet, (host, port))
            return self.socket.recv(1024)
        except socket.gaierror:
            logging.debug('Socket gaierror. Try next URL')
            return None
            # try next thingy

    #### TCP METHODS ####
    def construct_tracker_url(self, announce_url):
        """ Construct the full URL for the tracker server we're connecting to """ 
        params = '&'.join('%s=%s' % (key, U.quote(self.params[key])) 
                for key in self.params_order)
        tracker_url = announce_url + '?' +  params
        return tracker_url

    def send_request_and_parse_response(self):
        response = self.send_request_to_tracker_server()
        self.parse_response(response)
        return self.peers

    def send_request_to_tracker_server(self):
        """ Returns bencoded handshake request """
        logging.info('Request sent to tracker server.')
        return requests.get(url=self.tracker_url)

    def parse_response(self, response):
        logging.info('Response received from tracker, now parsing')
        response_text = B.bdecode(response.text)
        peer_ips = self.peers_to_ip_tuples(response_text['peers'])
        self.peers = peer_ips
        # return peer_ips

    def peer_host_port_vals(self, peers):
        #Get values of all bytes in byte_string list of peers
        peer_host_port_values = []
        while len(peers) > 0:
            peer_host_port_values.append([ord(peer) for peer in peers[0:6]])
            peers = peers[6:]
        return peer_host_port_values

    def get_host_string(self, peer_byte_list):
        return '.'.join([str(val) for val in peer_byte_list[0:4]])

    def get_port(self, peer_byte_list):
        return 256 * peer_byte_list[4] + peer_byte_list[5]

    def peers_to_ip_tuples(self, peer_bytes):
        byte_list = self.peer_host_port_vals(peer_bytes)
        return [(self.get_host_string(peer), self.get_port(peer)) for peer in byte_list]

    


def random_32_bit_int():
    return int(random.getrandbits(31))

def is_http_url(url):
    return 'http://' in url

def is_udp_url(url):
    return 'udp://' in url
