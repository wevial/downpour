import unittest
import hashlib
import os
from mock import MagicMock, patch
from StringIO import StringIO
from testfixtures import TempDirectory

from piece import Piece
from piece_queue import PieceQueue

test_dir = TempDirectory().path
fake_client = MagicMock()
#Testing piece implementation and methods
class TestPieceInitialization(unittest.TestCase):
    def test_piece_one_block(self):
        piece = Piece(fake_client, 1, 2**14, 'abc', test_dir)
        self.assertEqual(piece.num_blocks, 1)
        self.assertTrue(piece.not_all_blocks_requested()) 
        block_info = piece.get_next_block()
        self.assertEqual(block_info[0], 1)
        self.assertEqual(block_info[1], 0)
        self.assertEqual(block_info[2], 2**14)
        self.assertFalse(piece.not_all_blocks_requested())

    def test_piece_one_short_block(self):
        piece = Piece(fake_client, 1, 2, 'abcd', test_dir)
        self.assertEqual(piece.num_blocks, 1)
        self.assertTrue(piece.not_all_blocks_requested()) 
        block = piece.get_next_block()
        self.assertEqual(block[2], 2)
        self.assertFalse(piece.not_all_blocks_requested())

    def test_piece_two_blocks(self):
        piece = Piece(fake_client, 1, 2**14 + 2, 'abcd', test_dir)
        self.assertEqual(piece.num_blocks, 2)
        self.assertTrue(piece.not_all_blocks_requested()) 
        block = piece.get_next_block()
        self.assertTrue(piece.not_all_blocks_requested())
        block = piece.get_next_block()
        self.assertEqual(block[1], 2**14, '2nd block should begin at byte 2**14')
        self.assertEqual(block[2], 2, '2nd block should have length 2')
        self.assertFalse(piece.not_all_blocks_requested())

class TestPieceInfoHash(unittest.TestCase):
    def test_piece_info_hash(self):
        test_bytes = '\x00\x01\x02'
        test_hash = hashlib.sha1(test_bytes).digest()
        piece = Piece(fake_client, 1, 3, test_hash, test_dir)
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
        piece = Piece(fake_client, 1, 2**14 + 3, test_hash, test_dir)
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
        piece = Piece(fake_client, 1, 2**14 + 3, test_hash, test_dir)
        piece.write_file = StringIO()
        self.assertEqual(piece.num_blocks, 2)
        self.assertFalse(piece.check_if_finished())
        piece.add_block(2**14, test_bytes)
        self.assertFalse(piece.check_if_finished())
        piece.add_block(0, empty_block)
        self.assertTrue(piece.check_if_finished())
        self.assertTrue(piece.check_info_hash())
        
class TestPieceQueue(unittest.TestCase):
    def test_piece_queue_one_piece(self):
        test_bytes = '\x00'
        test_hash = hashlib.sha1(test_bytes).digest()
        piece = Piece(fake_client, 1, 1, test_hash, test_dir)
        piece_queue = PieceQueue([piece])
        test_piece = piece_queue.get_first_piece()
        self.assertEqual(test_piece.index, piece.index)

    def test_piece_queue_random(self):
        test_bytes = '\x00'
        test_hash = hashlib.sha1(test_bytes).digest()
        piece = Piece(fake_client, 1, 1, test_hash, test_dir)
        piece_queue = PieceQueue([piece])
        test_piece = piece_queue.get_next_random()
        self.assertEqual(test_piece.index, piece.index)
        test_piece.add_block(0, test_bytes)
        self.assertTrue(piece.check_if_finished())
        self.assertTrue(piece.check_info_hash())

    def test_piece_queue_random_two(self):
        test_bytes0 = '\x00'
        test_hash0 = hashlib.sha1(test_bytes0).digest()
        piece0 = Piece(fake_client, 0, 1, test_hash0, test_dir)
        test_bytes1 = '\x01'
        test_hash1 = hashlib.sha1(test_bytes1).digest()
        piece1 = Piece(fake_client, 1, 1, test_hash1, test_dir)
        pieces = [piece0, piece1]
        piece_queue = PieceQueue(pieces)
        test_piece = piece_queue.get_next_random()
        # print test_piece.index
        # print pieces[test_piece.index].index
        self.assertEqual(test_piece.index, pieces[test_piece.index].index)

    def test_piece_queue_random_five(self):
        pieces = []
        test_bytes_list = ['\x00', '\x01', '\x02', '\x03', '\x04']
        for i in range(5):
            test_bytes = test_bytes_list[i]
            test_hash = hashlib.sha1(test_bytes).digest()
            piece = Piece(fake_client, i, 1, test_hash, test_dir)
            pieces.append(piece)
        piece_queue = PieceQueue(pieces)
        for i in xrange(5):
            test_piece = piece_queue.get_next_random()
            self.assertEqual(test_piece.index, pieces[test_piece.index].index)

if __name__ == '__main__':
    unittest.main()
