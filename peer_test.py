import unittest
from message import Msg
#Would like to do this with mock instead of pulling one function out of peer and
# testing it by itself
from peer import Peer
from message import *
from mock import MagicMock

'''
class testSendMessage(unittest.TestCase):
    def test_send(self):
        mypeer = Peer('127.0.0.1', 6881)
        mypeer.socket
        mypeer.connect = MagicMock(returnvalue='None')
        mypeer.send = mock param => localvar
        mypeer.sendmessage(Msg('choke'))
        self.assertEqual(localvar, '\x00\x00\x00\x01\x00')
'''

client = MagicMock(returnvalue = 'None')

class TestBitfield(unittest.TestCase):
    def test_create_bitfield(self):
        client.num_pieces = 8
        mypeer = Peer('127.0.0.1', 6881, client)
        mypeer.act_on_messages((BitfieldMsg('\x00'),))
        self.assertEqual(mypeer.bitfield[0], 0)
        mypeer.act_on_messages((BitfieldMsg('\xff'),))
        self.assertEqual(mypeer.bitfield[0], 1)


class TestBuffer(unittest.TestCase):

    def test_init(self):
        mypeer = Peer('127.0.0.1', 6881, client)
        mypeer.buf = ''
        self.assertEqual(mypeer.buf, '')
        
    def test_init_nonempty(self):
        mypeer = Peer('127.0.0.1', 6881, client)
        mypeer.buf = '\x00'
        self.assertEqual(mypeer.buf, '\x00')

    def test_convert_keep_alive(self):
        mypeer = Peer('127.0.0.1', 6881, client)
        mypeer.buf = ''
        mypeer.process_and_act_on_incoming_data('\x00\x00\x00\xff\x00')
        self.assertEqual(mypeer.buf, '\x00\x00\x00\xff\x00')

    def test_buffer_plus_message_keep_alive(self):
        mypeer = Peer('127.0.0.1', 6881, client)
        mypeer.buf = ''
        mypeer.process_and_act_on_incoming_data('\x00\x00\x00\x00\x00')
        self.assertEqual(mypeer.buf, '\x00')

    def test_buffer_plus_message_unchoke(self):
        mypeer = Peer('127.0.0.1', 6881, client)
        mypeer.buf = ''
        mypeer.process_and_act_on_incoming_data('\x00\x00\x00\x01\x01\xff')
        self.assertEqual(mypeer.buf, '\xff')
        self.assertFalse(mypeer.peer_is_choking_client)


if __name__ == '__main__':
    unittest.main()
