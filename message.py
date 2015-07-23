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
        this.peer = peer
        this.client = client 
        
    def main(self):
        while len(buf) > 0:
            # Handshake is processed in the client
            if len(buf) < 4:
                continue
            msg_len, = struct.unpack('!I', buf[0:4])
            if msg_len == 0:
                # Keep alive message => prevent peer from timing out
                this.client.update_timeout(this.peer_id)
            elif len(buf) < msg_len:
                this.client.wait_for_rest_of_message(this.peer_id, buf)
                continue
            else:
                msg_id = struct.unpack('!B', buf[4])
                if msg_len == 1:
                    this.client.set_flag(this.peer_id, MESSAGE_FLAGS[msg_id])
                if msg_id == 4:
                    this.client.update_pieces(this.peer_id, 
                            struct.unpack('!I', buf[5:9]))
                if msg_id == 5:
                    this.client.update_bit_array(this.peer_id,
                            # TODO: Talk through the data structure for the bit array
                            # Modify this code accordingly
                            buf[5:5 + msg_len - 1])
                if msg_id == 6:
                    block_info = struct.unpack('!III', buf[5:17])
                    this.client.add_to_queue(this.peer_id, block_info)
                if msg_id == 7:
                    piece_index, block_index = struct.unpack('!II', buf[5:13])
                    block = struct.unpack('!'+str(msg_len-9)+'B', buf[13:])
                    this.client.add_block_to_piece(this.peer_id,
                            (piece_index, begin, len(block)), block)
                if msg_id == 8:
                    block_info = struct.unpack('!III', buf[5:17])
                    this.client.remove_from_queue(this.peer_id, block_info)
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


