import tracker
import socket
import sys

class Client:
    def __init__(self):
        pass

    def connect_to_peer(self, peer_ip, peer_port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print "Socket successfully created"
        except socket.error as err:
            print "Socket creation failed with error %s" %(err)

        port = 80 # default port

        try:
            host_ip = peer_ip
        except socket.gaierror:
            # This maeans could not resolve the host
            print "There was an issue resolving the host"
            sys.exit()

        # connecting to the server
        s.connect((peer_ip, peer_port))

        print "The socket has successfully connected to server"


