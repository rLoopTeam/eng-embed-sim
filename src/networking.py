#!/usr/bin/env python

# File:     networking.py
# Purpose:  Packet manipulation and networking functions for SafeUDP and communication with the FCU
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2017-Jan-17

# @see http://confluence.rloop.org/display/SD/UDP+Protocol

import sys
import socket
import threading
import struct
import logging
from collections import namedtuple

from config import Config

SpaceXPacket = namedtuple('SpaceXPacket', 
    ['team_id', 'status', 'acceleration', 'position', 'velocity', 'battery_voltage', 'battery_current', 'battery_temperature', 'pod_temperature', 'stripe_count'])

class PodComms:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
        self.logger = logging.getLogger("PodComms")

        # print self.config.nodes
        thismodule = sys.modules[__name__]

        self.nodes = {}
        self.port_node_map = {}   # Since we're using the ports and ignoring the ips, we can just map ports to nodes for handling
        for node_name, node_config in self.config.nodes.iteritems():
            handler_class = getattr(thismodule, node_config['handler'])
            self.nodes[node_name] = handler_class(self.sim, Config(node_config))  # Create node handler, e.g. FlightControlNode(self.sim, node_config)
            # @todo: add error checking for handler class creation
            #self.port_node_map[node_config['rx_port']] = self.nodes[node_name]  # Map rx ports to network nodes @todo: do we need this? Each one listens on its own port...
            self.port_node_map[node_config['tx_port']] = self.nodes[node_name]  # Map rx ports to network nodes @todo: do we need this? Each one listens on its own port...

    def eth_tx_callback(self, raw_tx_packet, length):
        """ Callback for the FCU to send data """
        bytes = b"".join(map(chr, raw_tx_packet[34:length]))  # Strip off the IPv4
        dest_port = struct.unpack('!H', bytes[2:4])[0]  # Get dest port from the UDP packet
        #print "Dest port is {} -- should be the node the FCU is trying to transmit to (e.g. 9100)".format(dest_port)
        # @todo: get the connection to use based on the destination port
        dest_node = self.port_node_map.get(dest_port, None)  # Find out where we want to send the packet by destination port (we only use ports for addressing)
        if dest_node is None:
            self.logger.debug("Got packet destined for port {} -- that's not a receive port for us, so we should probably send it.".format(dest_port))
        else:
            dest_addr = dest_node.tx_address
            dest_addr = ('127.255.255.255', dest_addr[1])  # Broadcast? Working on a way to get around the port binding issue (can't transmit out of python if bound on 127.0.0.1 and a port)
            #self.logger.debug("Bytes are {}".format(bytes))
            payload = bytes[8:]  # Strip off the UDP header (?)
            #self.logger.debug("PodComms.eth_tx_callback: using NetworkNode.send_udp() to get a packet back to the ground station")
            return self.port_node_map[dest_port].send_udp(payload, dest_addr)  # Send the UDP payload
    
    
    """

    def send_eth(self, pu8Buffer, u16BufferLength):
        # Send the ethernet packet -- extract the dest port and use the port_node_map to send the packet
        
        dest_port = None  # @todo: get this from the packet
        payload = None  # @todo: get this from the packet
        # @todo: there are a couple of different packet types. Should we (probably) pass it off to the appropriate node to do the sending? Yes.
        # Probably just send the whole buffer for it to handle
    """
    
    def run_threaded(self):
        # Start all of the nodes so they can listen on their rx_address
        for node in self.nodes.values():
            node.run_threaded()        
    

class NetworkNode:
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
        self.logger = logging.getLogger("NetworkNode")
        
        # Set up our addresses
        if self.sim.config.networking.force_loopback:
            self.host = "127.0.0.1"
        else:
            self.host = str(self.config.ip)

        self.rx_address = (self.host, self.config.rx_port)
        self.tx_address = (self.host, self.config.tx_port)

        self.buffer_len = 4096  # @todo: get this from config? Or just use 4096?

        # Enable/disable rx. These can be set in __init__ of subclasses (or elsewhere...)  @todo: maybe add enable/disable tx too? 
        self.enable_rx = True
        self.enable_tx = True

    def run_threaded(self):
        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()
        return t

    def run(self):
        """ Listen for udp packets on our rx address. We can also send UDP, but that doesn't require 'running' since we can just send them out """
        
        # Create a socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse addresses

        #self.clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        #self.clientSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

        # Bind the socket to the port
        try:
            if self.enable_rx:
                # bind_address = ('0.0.0.0', self.rx_address[1])  # Testing listening to get around issues
                bind_address = self.rx_address
                self.logger.debug('Listening to {} port {}'.format(*bind_address))
                #self.sock.bind(self.rx_address)  # This won't work -- packets don't get sent through to the GS if we bind to 127.0.0.1
                self.sock.bind(bind_address)
            else:
                self.logger.debug("(not) listening to {} port {}".format(*self.rx_address))
        except Exception as e:
            self.logger.error(e)

        while True and self.enable_rx:
            self.logger.debug('Waiting to receive message')
            data, source_address = self.sock.recvfrom(self.buffer_len)
    
            dest_address = self.rx_address  # We are the destination, so use our rx_port
            self.logger.debug('Received {} bytes from {}. Dest is {}'.format(len(data), source_address, dest_address))
            #print >>sys.stderr, data

            if data:
                # We've received a packet -- send it along to our overridden method for handling
                self.handle_udp_packet(data, source_address, dest_address)
                #self.logger.debug("Data received: {}".format([chr(x) for x in byte_array]))
    
    def recv_udp(self, packet, source_address):
        # @todo: is this used anywhere? We can maybe get rid of it (superseded by handle_udp_packet?)
        #self.logger.debug("Received packet: {} from {}".format([ str(x) for x in packet ]), source_address)  # verbose...
        self.logger.debug("Received {} bytes from {} (dropping them for lack of a handler)".format(len(packet), source_address))
                
        # By default, pass all UDP traffic to the FCU (@todo: is this right?)
        # @todo: not good that this knows about the FCU -- maybe pass this in as a callback? 
        #self.sim.fcu.handle_udp_packet(self, packet, source_address, self.rx_address)  # Note: self.rx_address is supplied by subclasses

    def handle_udp_packet(self, packet, source_address, dest_address):
        self.logger.debug("Handling UDP packet ({} bytes from {} to {} -- dropping for lack of a handler)".format(len(packet), source_address, dest_address))
        
    def send_udp(self, packet, dest_address):
        #self.logger.debug("Sending packet: {} to {}".format([ str(x) for x in packet ], dest_address))   # verbose...

        # TESTING -- works (but can't receive more packets, probably because we're resetting the socket and not binding back to it)
        #self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        ##self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse addresses -- not needed here
        #dest_address = ('127.0.0.1', 9100)
        # Packet that has been successfully received by the ground station via test_gs_accel_packets (generated by virtual FCU)
        #packet = "\xb1\x00\x00\x00\x03\x10\x3c\x00\x04\x00\x00\x00\x41\x01\xb0\x01\x1f\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x41\x01\xb0\x01\x1f\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf5\x46"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse addresses

        if self.enable_tx:
            self.logger.debug("(NetworkNode) Sending {} bytes to {}".format(len(packet), dest_address))
            #self.sock.sendto(packet, dest_address)
            sock.sendto(packet, dest_address)
        else:
            self.logger.debug("(not) sending {} bytes to {}".format(len(packet), dest_address))

        
class FlightControlNode(NetworkNode):
    def __init__(self, sim, config):
        NetworkNode.__init__(self, sim, config)
        self.logger = logging.getLogger("FlightControlNode")
    
        #self.rx_address = ('0.0.0.0', self.rx_address[1])
    
    def handle_udp_packet(self, packet, source_address, dest_address):
        self.logger.debug("handle_udp_packet called")
        if self.sim.config.fcu.enabled:
            #self.sim.fcu.handle_udp_packet(packet, source_address, self.rx_address)  # Note: self.rx_address is supplied by subclasses
            self.sim.fcu.handle_udp_packet(packet, source_address, self.tx_address)  # Note: using tx_address instead of rx address for the node since we're using different ports for the GS
        else:
            self.logger.debug("Handling UDP packet ({} bytes from {} to {} -- dropping since FCU is not enabled)".format(len(packet), source_address, dest_address))
    

    
class SpacexNode(NetworkNode):
    def __init__(self, sim, config):
        NetworkNode.__init__(self, sim, config)
        self.logger = logging.getLogger("SpacexNode")
        
        # Disable listening (we don't receive SpaceX packets, we only send them)
        self.enable_rx = False

    def handle_udp_packet(self, packet, source_address, dest_address):
        # Just send it out
        # @todo: do we need to filter out packets meant for the ground station? 
        self.send_udp(packet, dest_address)

# ----

class SpacexPacket:
    def __init__(self):
        pass
        
    @classmethod
    def send(cls, conn, payload_bytes):
        return "Sending SpacexPacket: {}".format([ str(x) for x in payload_bytes ])
        #return "Sending SpacexPacket: {}".format( payload_bytes )


class SafeUdpPacket:
    def __init__(self):
        pass

    @classmethod
    def send(cls, conn, payload_bytes):
        #return "Sending SafeUdpPacket: {}".format([ hex(x)[2:].zfill(2) for x in payload_bytes])
        #return "Sending SafeUDPPacket: {}".format([ str(x) for x in payload_bytes ])
        return "(not) sending SafeUDPPacket of {} bytes".format(len(payload_bytes))
        

class UdpListener(object):
    """ Listens for UDP traffic and takes action based on contents """

    def __init__(self, sim, config, callback):
        self.sim = sim
        self.config = config

        self.logger = logging.getLogger("FcuUdpListener")
        
        # Callback for passing the received packet
        self.callback = callback
        
        if self.sim.config.networking.force_loopback:
            self.address = "127.0.0.1"
        else:
            self.address = str(self.config.ip)
        print "FcuUdpListener.address: {}".format(self.address)
        self.port = self.config.rx_port
        self.buffer = 4096  # @todo: get this from config? Or just use 4096?


    def run_threaded(self):
        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()
        return t

    def run(self):
        # @todo: pipe this to the networking 
        
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

        #sock = socket.socket(socket.AF_INET, socket.SOCK_D, socket.IPPROTO_IP)

        # Bind the socket to the port
        server_address = (self.address, self.port)
        self.logger.debug('Starting up on %s port %s' % server_address)
        sock.bind(server_address)

        # RAW only
        #sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)  # Include IP headers
        #sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)   # Receive all

        while True:
            self.logger.debug('Waiting to receive message')
            data, address = sock.recvfrom(4096)
    
            dest_port = self.port  # We are the destination, so use our rx_port
            self.logger.debug('Received {} bytes from {}. Dest port is {}'.format(len(data), address, dest_port))
            #print >>sys.stderr, data
            
    
            if data:
                #self.callback(data)
                
                # Testing
                byte_array = bytearray(data)
                self.logger.debug("Data received: {}".format([chr(x) for x in byte_array]))
                #exit()
                #print 'We had data!' + str(b"".join(map(chr, data)))
                
                #sent = sock.sendto(data, address)
                #print >>sys.stderr, 'sent %s bytes back to %s' % (sent, address)


# @todo: deprecate this
class SafeUDP:    
    
    @classmethod
    def spacex_payload_from_eth2(cls, byte_sequence, length):
        bytes = b"".join(map(chr, byte_sequence[42:length]))
        return SpaceXPacket(*struct.unpack('!BBiiiiiiiI', bytes))
    
    
    @classmethod
    def from_eth_tx_callback(cls, byte_sequence, length):

        """
        - First 8 bytes are just on the wire, so you won't see that
        - 37 and 38 (?) are the destination port. Should be 9100. 
        - 43, 44, 45, and 46th are the sequence
        - 47 and 48 are the packet type
        - 49 and 50 are the payload length
        - [51:-2] is the payload
        - last 2 bytes are the CRC16
        """
        # Note: keep in mind python slicing numbering, e.g. a[12:14] gives you the 12th and 13th elements of a, or [a[12], a[13]]

        # Get an array of bytes representing the packet
        #return "len(byte_sequence): {}".format(len(byte_sequence))
        
        bytes = b"".join(map(chr, byte_sequence[0:length]))
        
        # Note: This was used to generate the packets used to see what's going on with this
        a = ["{}:{}".format(i, hex(x)[2:].zfill(2)) for i, x in enumerate(byte_sequence[0:length]) ]
        #a = ["{}".format(hex(x)[2:].zfill(2)) for x in byte_sequence[0:length] ]
        return " ".join( a )
        
        #return bytes
        
        # In the IPv4 section
        # Don't need anything from here
        
        # In the UDP section
        dest_port = struct.unpack('!H', bytes[36:38])  # Bytes 36 and 37 => unsigned short
        udp_length = struct.unpack('!H', bytes[38:40])[0] - 8  # Note: this is 8+payload length. The 8 bytes are the beginning of the UDP packet: source port, dest port, length, and checksum
        
        # In the SafeUDP section
        safeudp_pre = struct.unpack('!LHH', bytes[42:50])  #sequence (4 bytes => uint), packet type (2 bytes => ushort), safeudp payload length (2 bytes => ushort)
        safeudp_seq = safeudp_pre[0]
        safeudp_packet_type = safeudp_pre[1]
        safeudp_payload_length = safeudp_pre[2]
        
        return 
        return "Dest port: {}, SafeUDP Pre: {}".format(dest_port, safeudp_pre)
        
    def payload_from_eth2(cls, byte_sequence, length):
        #bytes = b"".join(map(chr, byte_sequence[0:length]))
        return byte_sequence[50:length]
        
        
if __name__ == "__main__":

    from sim import Sim

    config = Config()
    config.loadfile("conf/sim_config.yaml")

    sim = Sim(config.sim)
    
    #print config.sim.networking
        
    PodComms(sim, config.sim.networking)
    