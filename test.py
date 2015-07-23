import client as C
import peer as P


# Set things up...
print 'Setting up client and tracker...'
c = C.Client(C.TEST_TORRENT)
c.setup_client_and_tracker()

print 'Client, tracker set up.'
peers = c.peers
tom = P.Peer('96.126.104.219', 54465)
print 'List of peers (', len(peers), '):\n\t', peers
print "Hardcoded 'peer' to Tom's ip/port =", tom

print 'Sending handshake...'
handshake = c.send_and_receive_handshake(tom)
#handshake = c.send_and_receive_handshake(peers[0]) # Frank's
handshake = c.verify_handshake(handshake)
print 'Handshake verified'

