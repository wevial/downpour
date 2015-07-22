import peer
import select
MSG_LENGTH = 1024
# Event loop using select
# Simplifying assumptions:
# No cancellations
# Only concerned about peers received at beginning
# Not yet worrying about order implementation

class Reactor:
    # initialize with list of all peers
    def __init__(self, peer_list):
        self.sockets = [peer.socket
                for peer in peer_list]
        self.socket_ids = dict([(s, i) for i, s in enumerate(sockets)])
    def get_data(self):
        while self.sockets:
            rlist, _, _ = select.select(self.sockets, [], [])
            for sock in rlist:
                data = ''
                while True:
                    try:
                        new_data=sock.recv(MSG_LENGTH)
                    except socket.error as e:
                        if e.args[0] == errno.EWOULDBLOCK:
                            break
                        raise
                    else:
                        if not new_data:
                            break
                        else:
                            data += new_data
                if not data:
                    print 'no data'
                else:
                    socket_id = self.socket_ids[sock]
                    peer = peer_list[socket_id]
                    peer.raw_to_message(data)
                    
        

