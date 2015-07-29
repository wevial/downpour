import struct
import bitstring
import struct 


class Msg(object):
    #These class variables are the default, but may be overriden by subclass
    msg_len = 1
    pack_prefix = '!IB'
    def __init__(self, msg_name):
        if msg_name == 'keep_alive':
            self.pack_prefix = '!I'
            self.msg_len = 0
            self.msg_id = -1
        self.msg_name = msg_name 

    def get_message_contents(self):
        if self.msg_name == 'have':
            return self.piece_index,
        if self.msg_name == 'request':
            return self.block_info
        if self.msg_name == 'piece':
            return self.block_info[:2]

#Should these message-type specific pieces get extracted/abstracted?
#Maybe a unique class for each message type?
#There are two types of information here - index things & bytes

    def get_buffer_from_message(self):
        msg_len = self.msg_len
        msg_id = self.msg_id 
        pack_prefix = self.pack_prefix
        extras = self.get_message_contents()
        if msg_id == -1:
            return struct.pack(pack_prefix, msg_len)
        if not extras:
            return struct.pack(pack_prefix, msg_len, msg_id)
        return struct.pack(pack_prefix, msg_len, msg_id, 
                *(extras))

    @staticmethod
    def get_messages_from_buffer(buf):
        messages = []
        while len(buf) > 0:
            # Handshake is handled separately
            if len(buf) < 4:
                break
            
            msg_len = struct.unpack('!I', buf[0:4])[0]

            if msg_len == 0:
                # Keep alive message => prevent peer from timing out
                messages.append(Msg('keep_alive'))
            
            elif len(buf) < msg_len:
                # return from parse_buffer with message list & buf = buf
                break
            else:
                msg_id = struct.unpack('!B', buf[4])[0]
                if msg_len == 1:
                    if msg_id == 0:
                        messages.append(ChokeMsg())
                    if msg_id == 1:
                        messages.append(UnchokeMsg())
                    if msg_id == 2:
                        messages.append(InterestedMsg())
                    if msg_id == 3:
                        messages.append(UninterestedMsg())
                elif msg_id == 4:
                    piece_index, = struct.unpack('!I', buf[5:9])                   
                    messages.append( HaveMsg(piece_index = piece_index) )
                elif msg_id == 5:
                    bitfield_buf = buf[5:5 + msg_len - 1]
                    messages.append( BitfieldMsg(bitfield_buf = bitfield_buf) )
                elif msg_id == 6:
                    block_info = struct.unpack('!iii', buf[5:17])
                    messages.append( RequestMsg(block_info = block_info) ) 
                elif msg_id == 7:
                    piece_index, block_index = struct.unpack('!ii', buf[5:13])
                    block = buf[13:] # buffer is in bytes form, no need to unpack
                    block_info = (piece_index, block_index, len(block))
                    messages.append( BlockMsg(block_info = block_info, block = block) )
                elif msg_id == 8:
                    block_info = struct.unpack('!iii', buf[5:17])
                    messages.append( CancelMsg(block_info = block_info) )
            buf = buf[msg_len + 4:]
        return (messages, buf)


#To be refactored out of existence

class ChokeMsg(Msg):
    msg_id = 0
    def __init__(self):
        Msg.__init__(self, 'choke')

class UnchokeMsg(Msg):
    msg_id = 1
    def __init__(self):
        Msg.__init__(self, 'unchoke')

class InterestedMsg(Msg):
    msg_id = 2
    def __init__(self):
        Msg.__init__(self, 'interested')

class UninterestedMsg(Msg):
    msg_id = 3
    def __init__(self):
        Msg.__init__(self, 'uninterested')

class HaveMsg(Msg):
    msg_len = 5
    msg_id = 4
    pack_prefix = '!IBI'
    def __init__(self, piece_index):
        Msg.__init__(self, 'have')
        self.piece_index = piece_index

class BitfieldMsg(Msg):
    msg_len = 1
    msg_id = 5
    def __init__(self, bitfield_buf):
        Msg.__init__(self, 'bitfield')
        self.msg_len = self.msg_len + len(bitfield_buf)
        self.bitfield_buf = bitfield_buf

class RequestMsg(Msg):
    msg_id = 6
    msg_len = 13
    pack_prefix = '!IBIII'
    def __init__(self, block_info):
        Msg.__init__(self, 'request')
        self.block_info = block_info

class BlockMsg(Msg):
    msg_id = 7
    msg_len = 9
    pack_prefix = '!IBII'
    def __init__(self, block_info, block):
        Msg.__init__(self, 'piece')
        self.msg_len = self.msg_len + len(block) 
        self.block_info = block_info
        self.block = block

class CancelMsg(Msg):
    msg_id = 8
    msg_len = 13
    pack_prefix = '!IBIII'
    def __init__(self, block_info):
        Msg.__init__(self, 'cancel')
        self.block_info = block_info

def receive_data(peer, amount_expected, block_size=4096):
    try:
        data_received = ''
        amount_received = 0
        while amount_received < amount_expected:
            data = peer.recv(block_size)
            data_received += data
            amount_received += len(data)
    finally:
        return data

