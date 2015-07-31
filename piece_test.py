import unittest
from mock import MagicMock

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


