import unittest
import hashlib
import os
from mock import MagicMock, patch
from StringIO import StringIO
from testfixtures import TempDirectory

from piece import Piece

test_dir = TempDirectory().path
#Testing piece implementation and methods
class TestPieceInitialization(unittest.TestCase):
    def test_piece_one_block(self):
        piece = Piece(1, 2**14, 'abc', test_dir)
        self.assertEqual(piece.num_blocks, 1)
        self.assertTrue(piece.not_all_blocks_requested()) 
        (block_info, peer) = piece.get_next_block_and_peer_to_request()
        self.assertEqual(peer, None)
        self.assertEqual(block_info[0], 1)
        self.assertEqual(block_info[1], 0)
        self.assertEqual(block_info[2], 2**14)
        self.assertFalse(piece.not_all_blocks_requested())

    def test_piece_(self):
        piece = Piece(1, 2**14 + 2, 'abcd', test_dir)
        self.assertEqual(piece.num_blocks, 2)
        self.assertTrue(piece.not_all_blocks_requested()) 
        self.assertEqual(piece.get_next_block_and_peer_to_request()[1], None)
        self.assertTrue(piece.not_all_blocks_requested())
        (block, peer) = piece.get_next_block_and_peer_to_request()
        self.assertEqual(block[1], 2**14, '2nd block should begin at byte 2**14')
        self.assertEqual(block[2], 2, '2nd block should have length 2')
        self.assertFalse(piece.not_all_blocks_requested())

    def test_piece_two_blocks(self):
        piece = Piece(1, 2**14 + 2, 'abcd', test_dir)
        self.assertEqual(piece.num_blocks, 2)
        self.assertTrue(piece.not_all_blocks_requested()) 
        self.assertEqual(piece.get_next_block_and_peer_to_request()[1], None)
        self.assertTrue(piece.not_all_blocks_requested())
        (block, peer) = piece.get_next_block_and_peer_to_request()
        self.assertEqual(block[1], 2**14, '2nd block should begin at byte 2**14')
        self.assertEqual(block[2], 2, '2nd block should have length 2')
        self.assertEqual(peer, None)
        self.assertFalse(piece.not_all_blocks_requested())

class TestPieceInfoHash(unittest.TestCase):
    def test_piece_info_hash(self):
        test_bytes = '\x00\x01\x02'
        test_hash = hashlib.sha1(test_bytes).digest()
        piece = Piece(1, 3, test_hash, test_dir)
        piece.write_file = StringIO()
        self.assertEqual(piece.num_blocks, 1)
        self.assertFalse(piece.check_if_finished())
        self.assertTrue(piece.not_all_blocks_requested())
        piece.add_block(0, test_bytes)
        self.assertTrue(piece.check_if_finished())
        self.assertTrue(piece.check_info_hash())

    def test_piece_info_hash_two_blocks(self):
        test_bytes = '\x00\x01\x02'
        empty_block = '\x00' * 2**14
        test_hash = hashlib.sha1(empty_block + test_bytes).digest()
        piece = Piece(1, 2**14 + 3, test_hash, test_dir)
        piece.write_file = StringIO()
        self.assertEqual(piece.num_blocks, 2)
        self.assertFalse(piece.check_if_finished())
        piece.add_block(0, empty_block)
        self.assertFalse(piece.check_if_finished())
        piece.add_block(2**14, test_bytes)
        self.assertTrue(piece.check_if_finished())
        self.assertTrue(piece.check_info_hash())

    def test_piece_info_hash_out_of_order(self):
        test_bytes = '\x00\x01\x02'
        empty_block = '\x00' * 2**14
        test_hash = hashlib.sha1(empty_block + test_bytes).digest()
        piece = Piece(1, 2**14 + 3, test_hash, test_dir)
        piece.write_file = StringIO()
        self.assertEqual(piece.num_blocks, 2)
        self.assertFalse(piece.check_if_finished())
        piece.add_block(2**14, test_bytes)
        self.assertFalse(piece.check_if_finished())
        piece.add_block(0, empty_block)
        self.assertTrue(piece.check_if_finished())
        self.assertTrue(piece.check_info_hash())
        
if __name__ == '__main__':
    unittest.main()
