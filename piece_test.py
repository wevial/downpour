import unittest
from mock import MagicMock
import StringIO
from hashlib import sha1

from piece import Piece

#Testing piece implementation and methods
class TestPieceInitialization(unittest.TestCase):
    def test_piece_one_block(self):
        piece = Piece(1, 2**14, 'abc')
        self.assertEqual(piece.num_blocks, 1)
        self.assertTrue(piece.not_all_blocks_requested()) 
        self.assertEqual(piece.get_next_block_and_peer_to_request()[1], None)
        self.assertFalse(piece.not_all_blocks_requested())

    def test_piece_two_blocks(self):
        piece = Piece(1, 2**14 + 2, 'abcd')
        self.assertEqual(piece.num_blocks, 2)
        self.assertTrue(piece.not_all_blocks_requested()) 
        self.assertEqual(piece.get_next_block_and_peer_to_request()[1], None)
        self.assertTrue(piece.not_all_blocks_requested())
        (block, peer) = piece.get_next_block_and_peer_to_request()
        self.assertEqual(block[1], 2**14, '2nd block should begin at byte 2**14')
        self.assertEqual(block[2], 2, '2nd block should have length 2')
        self.assertEqual(peer, None)
        self.assertFalse(piece.not_all_blocks_requested())

#Testing client/piece initialization based on length
class TestPieceInfoHash(unittest.TestCase):
    test_bytes = '\x01\x02\x03'
    empty_block = '\x00' * 2**14

    def test_one_block_write(self):
        sha1_test = sha1(test_bytes).digest()
        piece = Piece(1, 3, sha1_test)
        self.assertEqual(piece.num_blocks, 1)
        # TODO: Use patch instead?
        piece.write_file = StringIO.StringIO()
        piece.update_block_count()
        self.assertTrue(piece.check_if_finished())
        self.write_block_to_file(0, '\x00\x01\x02')
        self.assertTrue(piece.check_info_hash())

    def test_two_block_write(self):
        sha1_test = sha1(empty_block + test_bytes).digest()
        piece = Piece(1, 2**14 + 3, sha1_test)
        self.assertEqual(piece.num_blocks, 2)
        piece.write_file = StringIO.StringIO()
        piece.update_block_count()
        self.assertFalse(piece.check_if_finished())
        self.write_block_to_file(0, empty_block)
        piece.update_block_count()
        self.write_block_to_file(16384, '\x00\x01\x02')
        self.assertTrue(piece.check_if_finished())
        self.assertTrue(piece.check_info_hash())

    def test_out_of_order_write(self):
        sha1_test = sha1(empty_block + test_bytes).digest()
        piece = Piece(1, 2**14 + 3, sha1_test)
        self.assertEqual(piece.num_blocks, 2)
        piece.write_file = StringIO.StringIO()
        piece.update_block_count()
        self.write_block_to_file(16384, '\x00\x01\x02')
        self.assertFalse(piece.check_if_finished())
        piece.update_block_count()
        self.write_block_to_file(0, empty_block)
        self.assertTrue(piece.check_if_finished())
        self.assertTrue(piece.check_info_hash())

        


