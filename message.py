def receive_data(peer, amount_expected, block_size=16):
    try:
        data_recieved = ''
        amount_recieved = 0
        while amount_recieved < amount_expected:
            data = peer.recv(block_size)
            data_recieved += data
            amount_recieved += len(data)
    finally:
        return data
