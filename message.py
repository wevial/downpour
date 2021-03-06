import struct

BLOCK_LENGTH = 2 ** 14


class Msg(object):
    # These class variables are the default, but may be overriden by subclass

    info_to_pack = ('!IB', 1)
    def __init__(self, msg_name, msg_id):
        self.msg_name = msg_name
        self.msg_id = msg_id

    # These are the only two outward facing functions
    def get_buffer_from_message(self):
        buffer_to_send = getattr(self, 'buffer_to_send', '')
        return struct.pack(*self.info_to_pack) + buffer_to_send

    @staticmethod
    def get_messages_from_buffer(buf):
        messages = []
        while len(buf) > 0:
            # Handshake is handled separately
            if len(buf) < 4:
                break
            msg_len = struct.unpack('!I', buf[:4])[0]
            if msg_len == 0:
                # Keep alive message => prevent peer from timing out
                messages.append(KeepAliveMsg())

            elif len(buf) < msg_len:
                # return from parse_buffer with message list & buf = buf
                break
            else:
                msg_id = struct.unpack('!B', buf[4])[0]
                if msg_id == 0:
                    messages.append(ChokeMsg())
                elif msg_id == 1:
                    messages.append(UnchokeMsg())
                elif msg_id == 2:
                    messages.append(InterestedMsg())
                elif msg_id == 3:
                    messages.append(UninterestedMsg())
                elif msg_id == 4:
                    piece_index, = struct.unpack('!I', buf[5:9])
                    messages.append(HaveMsg(piece_index=piece_index))
                elif msg_id == 5:
                    bitfield_buf = buf[5: msg_len + 4]
                    messages.append(BitfieldMsg(bitfield_buf=bitfield_buf))
                elif msg_id == 6:
                    block_info = struct.unpack('!III', buf[5:17])
                    messages.append(RequestMsg(block_info=block_info))
                elif msg_id == 7:
                    piece_index, block_begin = struct.unpack('!II', buf[5:13])
                    block_length = msg_len - 9
                    block = buf[13:msg_len + 4]  # buffer is in bytes form, no need to unpack
                    block_info = (piece_index, block_begin, block_length)

                    messages.append(BlockMsg(block_info=block_info, block=block))
                elif msg_id == 8:
                    block_info = struct.unpack('!III', buf[5:17])
                    messages.append(CancelMsg(block_info=block_info))
            buf = buf[msg_len + 4:]
        return (messages, buf)  # buf is remaining unprocessed bytes


class KeepAliveMsg(Msg):
    def __init__(self):
        msg_id = -1
        Msg.__init__(self, 'keep_alive', msg_id)
        self.info_to_pack = ('!I', 0)

    def __repr__(self):
        return 'keep alive'


class ChokeMsg(Msg):
    def __init__(self):
        msg_id = 0
        Msg.__init__(self, 'choke', msg_id)
        self.info_to_pack = self.info_to_pack + (msg_id,)

    def __repr__(self):
        return 'choke'


class UnchokeMsg(Msg):
    def __init__(self):
        msg_id = 1
        Msg.__init__(self, 'unchoke', msg_id)
        self.info_to_pack = self.info_to_pack + (msg_id,)

    def __repr__(self):
        return 'unchoke'


class InterestedMsg(Msg):
    def __init__(self):
        msg_id = 2
        Msg.__init__(self, 'interested', msg_id)
        self.info_to_pack = self.info_to_pack + (msg_id,)

    def __repr__(self):
        return 'interested'


class UninterestedMsg(Msg):
    def __init__(self):
        msg_id = 3
        Msg.__init__(self, 'uninterested', msg_id)
        self.info_to_pack = self.info_to_pack + (msg_id,)

    def __repr__(self):
        return 'uninterested'


class HaveMsg(Msg):
    def __init__(self, piece_index):
        msg_id = 4
        Msg.__init__(self, 'have', msg_id)
        self.piece_index = piece_index
        self.info_to_pack = ('!IBI', 5, 4, piece_index)

    def __repr__(self):
        return 'Have'


class BitfieldMsg(Msg):
    msg_len = 1

    def __init__(self, bitfield_buf):
        msg_id = 5
        self.msg_len = self.msg_len + len(bitfield_buf)
        Msg.__init__(self, 'bitfield', msg_id)
        self.buffer_to_send = bitfield_buf
        self.info_to_pack = ('!IB', self.msg_len, msg_id)

    def __repr__(self):
        return 'Bitfield'


class RequestMsg(Msg):
    msg_len = 13
    pack_prefix = '!IBIII'

    def __init__(self, block_info):
        msg_id = 6
        Msg.__init__(self, 'request', msg_id)
        self.block_info = block_info
        self.info_to_pack = (self.pack_prefix, self.msg_len, msg_id) + block_info

    def __repr__(self):
        return 'Request for piece ' + str(self.block_info[0]) + ' length ' + str(self.block_info[2])


class BlockMsg(Msg):
    msg_len = 9
    pack_prefix = '!IBII'

    def __init__(self, block_info, block):
        msg_id = 7
        Msg.__init__(self, 'piece', msg_id)
        self.msg_len = self.msg_len + len(block)
        self.buffer_to_send = block
        self.block_info = block_info
        self.info_to_pack = (self.pack_prefix, self.msg_len, msg_id) + block_info[:2]

    def __repr__(self):
        return 'Block'


class CancelMsg(Msg):
    msg_len = 13
    pack_prefix = '!IBIII'

    def __init__(self, block_info):
        msg_id = 8
        Msg.__init__(self, 'cancel', msg_id)
        self.block_info = block_info
        self.info_to_pack = (self.pack_prefix, self.msg_len, msg_id) + self.block_info

    def __repr__(self):
        return 'Cancel'


def receive_data(peer, amount_expected, block_size=4096):
    assert amount_expected > 0
    try:
        data_received = ''
        amount_received = 0
        while amount_received < amount_expected:
            data = peer.recv(block_size)
            data_received += data
            amount_received += len(data)
    finally:
        return data
