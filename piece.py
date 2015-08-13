from __future__ import division
import hashlib as H
import random
import os
import logging
import message
import math

BLOCK_LENGTH = 2 ** 14
MAX_REQUESTS = 10

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
        self.start_index = index * length
        self.write_file_path = os.path.join(dload_dir, 'torrtemp')

    def __cmp__(self, other):
        '''For purpose of sorting in order of increasing rarity'''
        return other.frequency - self.frequency

    def __repr__(self):
        return str(self.index)

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

    # EXPOSED METHOD: Called by client, dispatches to peer
    def cancel_block(self, block_info, peer_received_from):
        for peer in self.peers:
            if peer is not peer_received_from:
                peer.send_cancel_message(block_info)

    def request_block(self, block_info):
        peer = self.get_available_peer()
        peer.add_request_to_queue(block_info)

    def request_block_endgame(self, block_info):
        for peer in self.peers:
            peer.add_request_to_queue(block_info)

    def request_all_blocks(self):
        while self.not_all_blocks_requested():
            peer = self.get_available_peer()
            if peer:
                block_info = self.get_next_block()
                peer.add_request_to_queue(block_info)
            else:
                logging.warning('No peers available for piece %s', self.index)
                raise IndexError

    def get_available_peer(self):
        peer = self.peers[0]
        if len(peer.request_q) < MAX_REQUESTS:
            return peer
        else:
            # Am not calling this recursively to get default return none behavior
            self.peers.sort()
            peer = self.peers[0]
            if len(peer.request_q) < MAX_REQUESTS:
                return peer

    def get_next_block(self):
        if self.blocks_requested == self.num_blocks:
            raise IndexError('All blocks requested')
        logging.debug('Getting block %s of %s', self.blocks_requested, self.num_blocks)
        begin = self.blocks_requested * BLOCK_LENGTH
        if self.blocks_requested == self.num_blocks - 1:
            length = self.length - self.blocks_requested * BLOCK_LENGTH
            logging.info('Calculating length of last block: %s', length)
        else:
            length = BLOCK_LENGTH # This is another repetitive assignment
        self.blocks_requested += 1
        block_info = (self.index, begin, length)
        return block_info

    def write_block_to_file(self, begin, block):
        print 'Writing to piece', self.index, 'at position', begin + self.start_index
        begin = self.start_index + begin
        with open(self.write_file_path, 'r+b') as write_file:
            write_file.seek(begin)
            write_file.write(block)

    def check_info_hash(self):
        with open(self.write_file_path, 'r') as write_file:
            write_file.seek(self.start_index)
            file_bytes = write_file.read(self.length)
        computed_hash = H.sha1(file_bytes).digest()
        logging.debug('Checking piece hash for piece %s', self.index)
        logging.debug('Real - %s, computed - %s', self.piece_hash, computed_hash)
        return computed_hash == self.piece_hash

    # CALLS CLIENT
    def save_or_delete(self):
        if self.check_info_hash():
            logging.debug('Awesome, info hash for piece %s is correct', self.index)
            self.client.add_piece_to_bitfield(self.index)
        else:
            logging.warning('Incorrect info hash for piece %s', self.index)
            self.reset()

    def reset(self):
        self.blocks_received = 0
        self.blocks_requested = 0
#        self.create_write_file()

    # EXPOSED METHOD
    def add_block(self, begin, block):
        self.update_blocks_received()
        self.write_block_to_file(begin, block)
        if self.check_if_finished():
            self.save_or_delete()
