import struct
import bitstring

MESSAGE_FUNCTIONS = {
        0: peer_is_choking_client,
        1: peer_is_unchoking_client,
        2: peer_is_interested,
        3: peer_is_uninterested,
        }

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

def decode_msg(buf):
    # read 4 bytes
    if len(buf) < 4:
        print 'Buffer less than 4 bytes long'
        return None
    try:
        len_prefix = struct.unpack('!I', buf[:4])[0]
        if len_prefix == 0:
            print 'its a keep alive!'
        elif len(buf) > 4:
            msg_id = struct.unpack('!B', buf[4])[0]
            MESSAGE_FUNCTIONS[msg_id]()
            
    finally:
        pass

# Eventually add a flag with msg_id
def peer_is_choking_client(peer):
    peer.peer_is_choking_client = True

def peer_is_unchoking_client(peer):
    peer.peer_is_choking_client = False

def peer_is_interested(peer):
    peer.peer_is_interested = True

def peer_is_uninterested(peer):
    peer.peer_is_interested = False


