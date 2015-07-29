import unittest
from message import Msg
#Would like to do this with mock instead of pulling one function out of peer and
# testing it by itself
from peer import Peer
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
class testBuffer(unittest.TestCase):
    def test_init(self):
        mypeer = Peer('127.0.0.1', 6881)
        mypeer.buf = ''
        self.assertEqual(mypeer.buf, '')
    def test_init_nonempty(self):
        mypeer = Peer('127.0.0.1', 6881)
        mypeer.buf = '\x00'
        self.assertEqual(mypeer.buf, '\x00')
    def test_convert_bytes(self):
        mypeer = Peer('127.0.0.1', 6881)
        mypeer.buf = ''
        mypeer.convert_bytes_to_messages('\x00\x00\x00\xff\x00')
        self.assertEqual(mypeer.buf, '\x00\x00\x00\xff\x00')
    def test_buf_plus_message(self):
        mypeer = Peer('127.0.0.1', 6881)
        mypeer.buf = ''
        mypeer.convert_bytes_to_messages('\x00\x00\x00\x00\x00')
        self.assertEqual(mypeer.buf, '\x00')


if __name__ == '__main__':
    unittest.main()
