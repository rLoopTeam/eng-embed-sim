#!/usr/bin/env python

from bitarray import bitarray

class FaultType:
    def __init__(self, key, desc, subsystem):
        self.code = -1
        self.key = key
        self.desc = desc
        self.subsystem = subsystem

class ComponentFault:
    def __init__(self, fault, component, index):
        self.fault = fault   # Or fault code
        self.component = component
        self.component_index = index

class NormativeFault:
    def __init__(self, fault_type, causes):
        self.fault_type = fault_type
        self.causes = causes  # List of faults that caused this fault (e.g. lost_nav causes = lost_height_sensor[0], lost_height_sensor[1], lost_accel[0])




class Faults:
    def __init__(self, fault_bitarray):
        self.faults = fault_bitarray


def add_fault(fault, fault_list):
    """ Add a fault to the fault list and assign its code """
    index = len(fault_list)
    fault_list.append(fault)
    fault.code = index


def handle_something_fault(fault_flags, fault_list, mutable_fault_return):
    """ Handle the fault and return a list of fault_flags with the handled ones cleared. """
    # But how do we indicate that a fault has children? E.g. LOST_TOO_MANY_HEIGHT_SENSORS should own at least two height sensor faults
    # What about fault components? E.g. temperature sensor #432 on the battery is reading too high? how about if #432 and #434 are reading high?

current_fault_flags = bitarray()