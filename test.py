import client as C
import metainfo as M
import tracker as T
import peer as P

# Set things up...
print 'Setting up metainfo, tracker...'
m = M.Metainfo()
m.decode()
#print m.data

t = T.Tracker(m)
t.construct_url()
t.parse_response(t.send_request())
print 'metainfo, tracker set up.'
peers = t.peers
tom = P.Peer('96.126.104.219', 63529)
print 'List of peers:\n\t', peers
print "Hardcoded 'peer' to Tom's ip/port =", tom

print 'Setting up client...'
c = C.Client(m, t)
c.build_handshake()

print 'Sending handshake...'
handshake = c.send_handshake(tom)
print 'Handshake sent.'
#handshake = c.send_handshake(peers[0]) # Frank's
handshake = c.parse_handshake(handshake)

