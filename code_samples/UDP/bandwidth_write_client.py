#!/usr/bin/env python

from __future__ import division

import socket
import sys
import time

#!/usr/bin/env python

import socket
import sys

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('localhost', 10000)
message = 'This is the message.  It will be repeated.'

while True:
    try:

        # Send data
        print >>sys.stderr, 'sending "%s"' % message
        sent = sock.sendto(message, server_address)

        # Receive response
        print >>sys.stderr, 'waiting to receive'
        data, server = sock.recvfrom(4096)
        print >>sys.stderr, 'received "%s"' % data

    finally:
        print >>sys.stderr, 'closing socket'
        sock.close()

"""

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('localhost', 10000)
message = 'This is the message.  It will be repeated. '

t0 = time.clock()

time_limit = 10.0

counter = 0
while time.clock() - t0 <= time_limit:
    try:

        # Send data
        print >>sys.stderr, 'sending "%s"' % message
        sent = sock.sendto(message, server_address)
        counter += 1
        time.sleep(0.01)
        
        # Receive response
        #print >>sys.stderr, 'waiting to receive'
        #data, server = sock.recvfrom(4096)
        #print >>sys.stderr, 'received "%s"' % data

    finally:
        print >>sys.stderr, 'closing socket'
        sock.close()
        
print "Sent {} messages in {} seconds ({} messages/second)".format(counter, time_limit, counter / time_limit)

"""