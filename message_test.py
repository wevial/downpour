from message import Msg, BitfieldMsg, HaveMsg, RequestMsg, ChokeMsg, UnchokeMsg, InterestedMsg, UninterestedMsg
import unittest

class TestKeepAlive(unittest.TestCase):
    def test_keep_alive_name(self):
        keep_alive = Msg('keep_alive')
        self.assertEqual(keep_alive.msg_name, 'keep_alive')

    def test_keep_alive_no_id(self):
        keep_alive = Msg('keep_alive')
        with self.assertRaises(AttributeError):
            keep_alive.msg_id

    def test_parse_keep_alive(self):
        (keep_alive, buf) = Msg.get_messages_from_buffer('\x00\x00\x00\x00')
        self.assertEqual(keep_alive[0].msg_name, 'keep_alive')

    def test_parse_keep_alive_extra_bytes(self):
        (keep_alive, buf) = Msg.get_messages_from_buffer('\x00\x00\x00\x00\x01')
        self.assertEqual(buf, '\x01')
        
class TestChoke(unittest.TestCase):
    def test_choke_name(self):
        choke = ChokeMsg()
        self.assertEqual(choke.msg_name, 'choke')
    def test_choke_id(self):
        choke = ChokeMsg()
        self.assertEqual(choke.msg_id, 0)
    def test_parse_choke_from_buffer(self):
        (msgs, buf) = Msg.get_messages_from_buffer('\x00\x00\x00\x01\x00')
        self.assertEqual(msgs[0].msg_name, 'choke')

class TestBitField(unittest.TestCase):
    def test_bitfield_name(self):
        bitfield = BitfieldMsg(**{'bitfield_buf': '\x00\xff'})
        self.assertEqual(bitfield.msg_name, 'bitfield')
    def test_bitfield_buf(self):
        bitfield = BitfieldMsg(**{'bitfield_buf': '\x00\xff'})
        self.assertEqual(bitfield.bitfield_buf, '\x00\xff')
    def test_bitfield_buf_no_piece_index(self):
        bitfield = BitfieldMsg(**{'bitfield_buf': '\x00\xff'})
        with self.assertRaises(AttributeError):
            bitfield.piece_index


class TestHave(unittest.TestCase):
    def test_have_piece_index(self):
        have = HaveMsg(**{'piece_index': 17})
        self.assertEqual(have.piece_index, 17)

    def test_parse_have_is_message(self):
        (msgs, buf) = HaveMsg.get_messages_from_buffer('\x00\x00\x00\x05\x04\x00\x00\x00\x11')
        self.assertEqual(msgs[0].piece_index, 17)
    def test_get_contents(self):
        have = HaveMsg( **{'piece_index': 17})
        self.assertEqual(have.get_message_contents(), (17,))

class TestRequest(unittest.TestCase):
    def test_have_block_info(self):
        request = RequestMsg( **{'block_info': (5, 3701, 2600)})
        self.assertEqual(request.block_info,  (5, 3701, 2600))

    def test_get_contents(self):
        request = RequestMsg( **{'block_info': (5, 3701, 2600)})
        self.assertEqual(request.get_message_contents(), (5, 3701, 2600))

class TestBufferToMessage(unittest.TestCase):
    def test_choke_to_buffer_and_back(self):
        choke = ChokeMsg()
        choke_buf = choke.get_buffer_from_message()
        self.assertEqual(choke_buf,
                Msg.get_messages_from_buffer(choke_buf)[0][0].get_buffer_from_message())

#Test message construction

#Test message parsing
if __name__ == '__main__':
    unittest.main()
