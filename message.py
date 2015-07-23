import struct
import bitstring
import struct 

MESSAGE_FLAGS = {
        0: 'choke',
        1: 'unchoke',
        2: 'interested',
        3: 'uninterested',
        4: 'have',
        5: 'bitfield',
        6: 'request',
        7: 'piece',
        8: 'cancel'
        }

class MessageParser(object):
    def __init__(self, client, peer):
        self.peer = peer
        self.client = client 
        
    def main(self):
        while len(buf) > 0:
            # Handshake is processed in the client
            if len(buf) < 4:
                if not self.peer.check_is_still_alive():
                    break # Do something later to kill the peer
                continue

            msg_len = struct.unpack('!I', buf[0:4])[0]

            if msg_len == 0:
                # Keep alive message => prevent peer from timing out
                self.peer.continue_living()
            elif len(buf) < msg_len:
                self.client.wait_for_rest_of_message(self.peer_id, buf)
                continue
            else:
                msg_id = struct.unpack('!B', buf[4])[0]
                if msg_len == 1:
                    self.client.set_flag(self.peer_id, MESSAGE_FLAGS[msg_id])
                elif msg_id == 4:
                    self.client.update_pieces(self.peer_id, 
                            struct.unpack('!I', buf[5:9]))
                elif msg_id == 5:
                    self.client.update_bit_array(self.peer_id,
                            # TODO: Talk through the data structure for the bit array
                            # Modify this code accordingly
                            buf[5:5 + msg_len - 1])
                elif msg_id == 6:
                    block_info = struct.unpack('!III', buf[5:17])
                    self.client.add_to_queue(self.peer_id, block_info)
                elif msg_id == 7:
                    piece_index, block_index = struct.unpack('!II', buf[5:13])
                    block = struct.unpack('!'+str(msg_len-9)+'B', buf[13:])
                    self.client.add_block_to_piece(self.peer_id,
                            (piece_index, begin, len(block)), block)
                elif msg_id == 8:
                    block_info = struct.unpack('!III', buf[5:17])
                    self.client.remove_from_queue(self.peer_id, block_info)
            buf = buf[msg_len + 4:]

# Old functions, likely to be deleted / edited extensively

def receive_data(peer, amount_expected, block_size=4096):
    try:
        data_recieved = ''
        amount_recieved = 0
        while amount_recieved < amount_expected:
            data = peer.recv(block_size)
            data_recieved += data
            amount_recieved += len(data)
    finally:
        return data


