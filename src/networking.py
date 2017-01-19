#!/usr/bin/env python

# File:     networking.py
# Purpose:  Packet manipulation and networking functions for SafeUDP and communication with the FCU
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2017-Jan-17

# @see http://confluence.rloop.org/display/SD/UDP+Protocol

import sys
import struct
from collections import namedtuple

from config import Config

SpaceXPacket = namedtuple('SpaceXPacket', 
    ['team_id', 'status', 'acceleration', 'position', 'velocity', 'battery_voltage', 'battery_current', 'battery_temperature', 'pod_temperature', 'stripe_count'])

PodCommNode = namedtuple('PodCommNode', 
    ['name', 'handler', 'ip', 'tx_port', 'rx_port', 'MAC'])

class PodComms:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config

        # print self.config.nodes
        thismodule = sys.modules[__name__]

        self.nodes = {}
        self.packet_type_map = {}
        for k, node in self.config.nodes.iteritems():
            self.nodes[k] = PodCommNode(**node)
            # @todo: add error checking for handler class creation
            self.packet_type_map[node['tx_port']] = {'node': k, 'handler': getattr(thismodule, node['handler'])()}

    def send(self, raw_tx_packet, length):
        bytes = b"".join(map(chr, raw_tx_packet[36:length]))
        dest_port = struct.unpack('!H', bytes[0:2])[0]
        # @todo: get the connection to use based on the destination port
        conn = None
        return self.packet_type_map[dest_port]['handler'].send(conn, bytes[6:])
        

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
        return "Sending SafeUdpPacket: {}".format([ hex(x)[2:].zfill(2) for x in payload_bytes])
        

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
    