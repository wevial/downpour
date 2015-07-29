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
            self.register_reader(peer.socket, peer.process_and_act_on_incoming_data)

    def register_reader(self, socket, callback):
        self.sockets.append(socket)
        self.readers[socket] = callback
    
    def get_data(self):
        while self.sockets:
            self.read_from_live_sockets()

    def read_from_live_sockets(self):
        rlist, _, _ = select.select(self.sockets, [], [])
        for socket in rlist:
            data = self.read_all(socket)
            print data
            self.readers[socket](data)
        
    @staticmethod
    def read_all(socket):
        data = ''
        while True:
            try:
                new_data = socket.recv(MSG_LENGTH)
            except socket.error as e:
                if e.args[0] == errno.EWOULDBLOCK:
                    break
                raise IOError('WTF SOCKET: Something went wrong with the socket')
            else:
                if not new_data:
                    break
                print 'more data!'
                print data
                data += new_data
                print 'MOAR DATA', len(data)
        if not data:
            raise IOError('Reactor.read_all passed an empty socket') 
        return data
    

