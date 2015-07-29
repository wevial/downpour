import select
from message import Msg
MSG_LENGTH = 4096
# Event loop using select
# Simplifying assumptions:
# No cancellations
# Only concerned about peers received at beginning
# Not yet worrying about order implementation

class Reactor:
    # initialize with list of all peers
    def __init__(self, peer_list):
        self.readers = {}
        self.sockets = []
        for peer in peer_list:
            self.register_reader(peer.socket, peer.convert_bytes_to_messages)

    def register_reader(self, socket, callback):
        self.sockets.append(socket)
        self.readers[socket] = callback
    
    def get_data(self):
        while self.sockets:
            self.read_from_live_sockets()

    def read_from_live_sockets(self):
        rlist, _, _ = select.select(self.sockets, [], [])
        for sock in rlist:
            data = self.read_all(sock)
            self.readers[sock](data)
        
    @staticmethod
    def read_all(sock):
        data = ''
        while True:
            try:
                new_data=sock.recv(MSG_LENGTH)
            except sock.error as e:
                if e.args[0] == errno.EWOULDBLOCK:
                    break
                raise
            else:
                if not new_data:
                    break
                else:
                    data += new_data
        if not data:
            raise IOError('read all passed an empty socket') 
        return data
    

