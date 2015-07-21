import client as C
import metadata as M
import tracker as T

# Set things up...
print 'Setting up metadata, tracker...'
m = M.Metadata()
m.decode()
#print m.data

t = T.Tracker(m)
t.construct_url()
t.parse_response(t.send_request())
print 'Metadata, tracker set up.'
peers = t.peer_ips
peer = ('96.126.104.219', 63529)
print 'List of peers:\n\t', peers
print "Hardcoded 'peer' to Tom's ip/port =", peer

print 'Setting up client...'
c = C.Client(m, t)

print 'Sending handshake...'
handshake = c.send_handshake(peer)
print 'Handshake sent.'
#handshake = c.send_handshake(peers[0]) # Frank's
handshake = c.parse_handshake(handshake)

