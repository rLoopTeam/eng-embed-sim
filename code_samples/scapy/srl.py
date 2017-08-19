#! /usr/bin/env python

# @see http://www.secdev.org/projects/scapy/build_your_own_tools.html

#from scapy.base_classes import Gen, SetGen
#import scapy.plist as plist
#from scapy.utils import PcapReader
#from scapy.data import MTU, ETH_P_ARP

#from scapy.all import 
#from scapy.base_classes import Gen, SetGen
#import scapy.plist as plist
#from scapy.utils import PcapReader
#from scapy.data import MTU, ETH_P_ARP
#import os,re,sys,socket,time, itertools
#WINDOWS = True



import sys
from scapy.all import IP,Ether,UDP

p=Ether() / IP(dst=sys.argv[1]) / UDP()
print p.show()