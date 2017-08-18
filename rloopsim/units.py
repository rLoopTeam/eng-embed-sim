#!/usr/bin/env python
# coding=UTF-8

# File:     units.py
# Purpose:  Units convenience methods
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2016-Dec-28

from pint import UnitRegistry

class Units:

    ureg = UnitRegistry()
        
    @classmethod
    def SI(cls, quantity_str):
        """ Convert to standard units """
        return cls.ureg.parse_expression(quantity_str).to_base_units().magnitude
            
    @classmethod
    def usec(cls, quantity_time):
        return cls.ureg.parse_expression(quantity_time).to(cls.ureg.microsecond).magnitude

    @classmethod
    def mm(cls, quantity_distance):
        return cls.ureg.parse_expression(quantity_distance).to(cls.ureg.millimeter).magnitude
      
    @classmethod  
    def seconds(cls, quantity_time):
        return cls.ureg.parse_expression(quantity_time).to(cls.ureg.seconds).magnitude
        
    
if __name__ == "__main__":
    a = ['1.25m', '3ft', '18psi', '4m/s', "100usec", '10min']
    for qty in a:
        print("{} => {}".format(qty, Units.SI(qty)))
        #print Units.SI(qty).magnitude