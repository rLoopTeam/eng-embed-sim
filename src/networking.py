#!/usr/bin/env python

# File:     networking.py
# Purpose:  Packet manipulation and networking functions for SafeUDP and communication with the FCU
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2017-Jan-17

# @see http://confluence.rloop.org/display/SD/UDP+Protocol

from config import Config
import struct
from collections import namedtuple

SpaceXPacket = namedtuple('SpaceXPacket', 
    ['team_id', 'status', 'acceleration', 'position', 'velocity', 'battery_voltage', 'battery_current', 'battery_temperature', 'pod_temperature', 'stripe_count'])

PodCommNode = namedtuple('PodCommNode', 
    ['name', 'ip', 'tx_port', 'rx_port', 'MAC'])

class PodComms:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config

        # print self.config.nodes

        self.nodes = {}
        self.packet_type_map = {}
        for k, node in self.config.nodes.iteritems():
            self.nodes[k] = PodCommNode(**node)
            self.packet_type_map[node.tx_port] = k  # @todo: make this useful. Should tell us how to interpret the packet/which class/function to use (maybe a fn ptr?)
        
    def _create_packet_type_map(self):
        pass


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
    config = Config()
    config.loadfile("conf/sim_config.yaml")
    
    print config.sim.networking
        
    PodComms(None, config.sim.networking)
    