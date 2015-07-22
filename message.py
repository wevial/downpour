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

class Message(object):
    def __init__(self, peer):
        this.peer = peer
        
    while len(buf) > 0:
        if check_for_handshake(buf):
            process_handshake
        msg_len, = struct.unpack('!I', buf[0:4])
        if msg_len == 0:
            update_timeout(peer)
            buf = buf[4:]
        if len(buf) < msg_len:
            wait_for_rest_of_message(buf)
        msg_id = struct.unpack('!B', buf[4])
        #These four are a pseudo-block, and if one is true, need to update
        #buffer and go back to top of while loop
        if msg_len == 1:
            if msg_id == 0:
                this.peer.am_choked = 1
            if msg_id == 1:
                this.peer.am_choked = 0
                send_piece_requests_to_peer(this.peer)
            if msg_id == 2:
                this.peer.interested = 1
                if ok_to_unchoke(this.peer):
                    send_message(this.peer, constructMessage('unchoke'))
            if msg_id == 3:
                this.peer.interested = 0
        if msg_id == 4:
            this.peer.update_peer_pieces(struct.unpack('!I', buf[5:9]))
        if msg_id == 5:
            this.peer.update_peer_bit_array(buf[5:5+msg_len - 1])
        if msg_id == 6:
            index, begin, length = struct.unpack('!III', buf[5:17])
            add_to_queue(index, begin, length)
        if msg_id == 7:
            index, begin = struct.unpack('!II', buf[5:13])
            block = struct.unpack('!'+str(msg_len-9)+'B', buf[13:])
            add_block_to_piece(index, begin, block)
        if msg_id == 8:
            index, begin, length = struct.unpack('!III', buf[5:17])
            remove_from_queue(index, begin, length)
        buf = buf[msg_len + 4:]

    
            
            



