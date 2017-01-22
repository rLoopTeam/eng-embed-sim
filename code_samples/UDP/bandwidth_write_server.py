#!/usr/bin/env python

import socket
import sys

import csv

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('localhost', 10000)
print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)

with open('bandwidth_write_test.txt', 'w') as f:
    writer = csv.writer(f)

    while True:
        print >>sys.stderr, '\nwaiting to receive message'
        data, address = sock.recvfrom(4096)
        print >>sys.stderr, '\nwriting row'
        writer.writerow([address, data])
        print "wrote row"
    
    if data:
        sent = sock.sendto(data, address)
        print >>sys.stderr, 'sent %s bytes back to %s' % (sent, address)
