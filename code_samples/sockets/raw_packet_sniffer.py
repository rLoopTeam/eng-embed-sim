#!/usr/bin/env python
import struct
import socket
import binascii
import sys

import admin
if not admin.isUserAdmin():
    admin.runAsAdmin()

#Packet sniffer in python
#For Linux
 
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)

address = "127.0.0.1"
port = 9100

# Bind the socket to the port
server_address = (address, port)
print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)

# RAW only
sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)  # Include IP headers
#sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)   # Receive all

# receive a packet
while True:
    print sock.recvfrom(65565)

while True:
    pass
  
exit()  
"""
rawSocket=  socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)

        server_address = (self.address, self.port)
        print >>sys.stderr, 'starting up on %s port %s' % server_address
        sock.bind(server_address)

        # RAW only
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)  # Include IP headers
        sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)   # Receive all

"""

#ifconfig eth0 promisc up
receivedPacket=rawSocket.recv(2048)
while True:
    pass
exit()

#Ethernet Header...
ethernetHeader=receivedPacket[0:14]
ethrheader=struct.unpack("!6s6s2s",ethernetHeader)
destinationIP= binascii.hexlify(ethrheader[0])
sourceIP= binascii.hexlify(ethrheader[1])
protocol= binascii.hexlify(ethrheader[2])
print "Destinatiom: " + destinationIP
print "Souce: " + sourceIP
print "Protocol: "+ protocol

#IP Header... 
ipHeader=receivedPacket[14:34]
ipHdr=struct.unpack("!12s4s4s",ipHeader)
destinationIP=socket.inet_ntoa(ipHdr[2])
print "Source IP: " +sourceIP
print "Destination IP: "+destinationIP

#TCP Header...
tcpHeader=receivedPacket[34:54]
tcpHdr=struct.unpack("!2s2s16s",tcpHeader)
sourcePort=socket.inet_ntoa(tcpHdr[0])
destinationPort=socket.inet_ntoa(tcpHdr[1])
print "Source Port: " + sourcePort
print "Destination Port: " + destinationPort


while True:
    pass