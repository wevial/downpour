from __future__ import division
import hashlib as H
import random
import os
import logging
import message
import math

BLOCK_LENGTH = 2 ** 14


class Piece(object):
    #Piece length is uniform across torrent (except last piece)
    #Number of blocks is uniform across torrent (except last piece)

    def __init__(self, client, index, length, piece_hash, dload_dir):
        self.length = length
        self.index = index
        self.piece_hash = piece_hash
        self.frequency = 0
        self.client = client
        self.peers = []
        self.num_blocks = math.ceil(self.length / BLOCK_LENGTH)  
        # print 'initialized piece: ', index, ' length ', length, ' # blocks ', self.num_blocks
        self.blocks_requested = 0
        self.blocks_received = 0
        self.dload_dir = dload_dir
        self.create_write_file()

    def __cmp__(self, other):
        '''For purpose of sorting in order of increasing rarity'''
        return other.frequency - self.frequency

    def __repr__(self):
        return str(self.index)

    def create_write_file(self):
        file_path = os.path.join(self.dload_dir, str(self.index))
        open(file_path, 'wa').close() # Create file if it does not exist
        self.write_file = open(file_path, 'r+b')

    def add_peer_to_peer_list(self, peer):
        self.frequency += 1
        self.peers.append(peer)

    def has_no_peers(self):
        return len(self.peers) == 0
    
    def not_all_blocks_requested(self):
        return self.blocks_requested < self.num_blocks

    def check_if_finished(self):
        return self.blocks_received == self.num_blocks

    def update_blocks_received(self):
        self.blocks_received += 1

    def cancel_block(self, block_info, peer_received_from):
        for peer in self.peers:
            if peer is not peer_received_from:
                peer.send_cancel_message(block_info)

    # TODO: Refactor these three semi-redundant methods
    def request_block_endgame(self, block_info):
        for peer in self.peers:
            peer.add_request_to_queue(block_info)

    def request_block(self, block_info):
        if self.has_no_peers():
            raise IndexError('Piece has no peers yet. Wait to send requests')
        peer = self.peers[0]
        peer.add_request_to_queue(block_info)

    def request_all_blocks(self):
        if self.has_no_peers():
            raise IndexError('Piece has no peers yet. Wait to send requests')
        self.peers.sort()  # Sorts by length of request queue
        peer_block_count = 0
        peer_index = 0
        peer = self.peers[peer_index]
        max_requests = max(10 - len(peer.request_q), 5)
        while self.not_all_blocks_requested():
            block_info = self.get_next_block()
            logging.info('queueing up message for block %s', block_info)
            if peer_block_count < max_requests:
                peer_block_count += 1
            else:
                peer_index += 1
                peer_block_count = 0
                peer = self.peers[peer_index]
            peer.add_request_to_queue(block_info)

    # TODO: Refactor this, it could be cleaner
    def get_next_block(self):
        logging.debug( 'Getting block ', self.blocks_requested, ' of ', self.num_blocks)
        begin = self.blocks_requested * BLOCK_LENGTH
        if self.blocks_requested == self.num_blocks - 1:
            length = self.length - self.blocks_requested * BLOCK_LENGTH
            logging.info('Calculating length of last block: %s', length)
        else:
            length = BLOCK_LENGTH # This is another repetitive assignment
        self.blocks_requested += 1
        block_info = (self.index, begin, length)
        return block_info

    # EXPOSED METHOD
    def add_block(self, begin, block):
        self.update_blocks_received()
        self.write_block_to_file(begin, block)
        if self.check_if_finished():
            self.save_or_delete()

    def write_block_to_file(self, begin, block):
        print 'Writing to piece', self.index, 'at position', begin
        self.write_file.seek(begin)
        self.write_file.write(block)

    def check_info_hash(self):
        self.write_file.seek(0)
        file_bytes = self.write_file.read()
        computed_hash = H.sha1(file_bytes).digest()
        logging.debug('Checking piece hash for piece %s', self.index)
        logging.debug('Real - %s, computed - %s', self.piece_hash, computed_hash)
        return computed_hash == self.piece_hash

    # CALLS CLIENT
    def save_or_delete(self):
        if self.check_info_hash():
            logging.debug('Awesome, info hash is correct')
            self.client.add_piece_to_bitfield(self.index)
        else:
            logging.warning('Incorrect info hash for piece %s', self.index)
            self.reset()

    def reset(self):
        self.blocks_received = 0
        self.blocks_requested = 0
        self.create_write_file()

    def check_if_finished(self):
        return self.blocks_received == self.num_blocks

    def update_block_count(self):
        self.blocks_received += 1

    def write_block_to_file(self, begin, block):
        print 'Writing to piece', self.index, 'at position', begin
        self.write_file.seek(begin)
        self.write_file.write(block)

    def add_block(self, begin, block):
        self.update_block_count()
        self.write_block_to_file(begin, block)
        if self.check_if_finished():
            self.save_or_delete()

    # Exposed method
    def get_next_block_and_peer_to_request(self):
        logging.debug('Getting block %s of %s.', self.blocks_requested, self.num_blocks)
        begin = self.blocks_requested * BLOCK_LENGTH
        if self.blocks_requested == self.num_blocks - 1:
            length = self.length - self.blocks_requested * BLOCK_LENGTH
            # TODO: Why is this getting printed for all blocks?
            logging.info('Calculating length of last block: %s', length)
        else:
            length = BLOCK_LENGTH # This is another repetitive assignment
        self.blocks_requested += 1
        block_info = (self.index, begin, length)
        if len(self.peers):
            peer = random.choice(self.peers)
        else:
            peer = None
            self.client.add_piece_to_queue(self)
        return (block_info, peer)
