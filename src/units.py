#!/usr/bin/env python

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
    
if __name__ == "__main__":
    a = ['1.25m', '3ft', '18psi', '4m/s', "100usec", '10min']
    for qty in a:
        print "{} => {}".format(qty, Units.SI(qty))
        #print Units.SI(qty).magnitude