import select
from message import Msg

MSG_LENGTH = 4096

# Event loop using select
# Simplifying assumptions:
# No cancellations
# Only concerned about peers received at beginning
# Not yet worrying about order implementation

class Reactor:
    def __init__(self, peer_list):
        # initialize with list of all peers
        self.readers = {}
        self.message_queues = {}
        self.sockets = []
        for peer in peer_list:
            self.register_reader(peer.socket, peer.process_and_act_on_incoming_data)
        for peer in peer_list:
            self.register_message_queue(peer.socket, peer.get_from_message_queue)

    def register_reader(self, socket, callback):
        self.sockets.append(socket)
        self.readers[socket] = callback
    
    def register_message_queue(self, socket, message_queue):
        self.message_queues[socket] = message_queue

    def get_data(self):
        while self.sockets:
            self.read_write_live_sockets()

    def read_write_live_sockets(self):
        rlist, wlist, _ = select.select(self.sockets, self.sockets, [])
        print wlist
        for socket in rlist:
            data = self.read_all(socket)
            if data:
                self.readers[socket](data)
        for sock in wlist:
            #TODO: Code below doesnt execute. Wlist is empty. 
            try:
                message = self.message_queues[socket]()
                print 'sending message of type ', message
                message_bytes = message.get_buffer_from_message()
            #TODO: Fix this error handling block, generic Error does not exist
            except Error as e:
                print e 
            else:
                sock.sendall(message_bytes)
        
    @staticmethod
    def read_all(socket):
        data = ''
        while True:
            try:
                new_data = socket.recv(MSG_LENGTH)
            #TODO: Error handling - socket has no error attribute
            except socket.error as e:
                if e.args[0] == errno.EWOULDBLOCK:
                    break
                raise IOError('WTF SOCKET: Something went wrong with the socket')
            else:
                if not new_data:
                    break
                data += new_data
                print 'Received data in the reactor. Data len:', len(new_data)
        # if not data:
            # raise IOError('Reactor.read_all passed an empty socket') 
        return data
    

