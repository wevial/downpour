from peer import Peer
from reactor import Reactor
import client as C

# Set things up...
print 'Setting up client and tracker...'
c = C.Client(C.TEST_TORRENT)
print 'Client, tracker set up.'

peers = c.peers
tom = Peer('96.126.104.219', 54465, c)
for peer in peers.values():
    print peer
    if peer.ip == '96.126.104.219':
        tom = peer
print 'List of peers (', len(peers), '):\n\t', peers
print "Hardcoded 'peer' to Tom's ip/port =", tom

print 'Sending handshake...'
t_handshake = tom.send_and_receive_handshake(c.handshake)
#handshake = c.send_and_receive_handshake(peers[0]) # Frank's
#handshake = tom.verify_handshake(t_handshake, c.info_hash)
print 'Handshake verified'
tom.verify_and_initiate_communication(t_handshake, c.info_hash)
# init reactor
c.reactor = Reactor([tom])
c.reactor.get_data()

