import select
import logging
import Queue

MSG_LENGTH = 4096

# Event loop using select
# Simplifying assumptions:
# No cancellations
# Only concerned about peers received at beginning
# Not yet worrying about order implementation


class Reactor:
    def __init__(self):
        # Initialize with empty list
        self.readers = {}
        self.message_queues = {}
        self.sockets = []

    def add_peer_socket(self, peer):
        self.sockets.append(peer.socket)
        self.register_reader(peer.socket, peer.process_and_act_on_incoming_data)
        self.register_message_queue(peer.socket, peer.get_from_message_queue)

    def register_reader(self, socket, callback):
        self.readers[socket] = callback

    def register_message_queue(self, socket, message_queue):
        self.message_queues[socket] = message_queue

    def get_data(self):
        while self.sockets:
            self.read_write_live_sockets()

    def read_write_live_sockets(self):
        socks = self.sockets
        rlist, wlist, _ = select.select(socks, socks, socks)
        logging.info('Scanning for readable sockets')
        for sock in rlist:
            data = self.read_all(sock)
            if data:
                self.readers[sock](data)
            else:
                logging.info('Nothing coming in')
        logging.info('Scanning for writable sockets')
        for sock in wlist:
            try:
                message = self.message_queues[sock]()
                message_bytes = message.get_buffer_from_message()
                sock.sendall(message_bytes)
            except Queue.Empty:
                logging.info('No messages in queue')

    @staticmethod
    def read_all(socket):
        data = ''
        try:
            new_data = socket.recv(MSG_LENGTH)
            if not new_data:
                logging.info('Theres no new data')
                pass
            else:
                data += new_data
                print 'Received data in the reactor. Data len:', len(new_data)
        except IOError as e:
            logging.warning('Error', e)
        return data
