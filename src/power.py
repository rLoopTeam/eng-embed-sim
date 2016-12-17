#!/usr/bin/env python

# @todo: complete this

class PowerSink:

    def __init__(self, volts, power_source):
        self.power_source = power_source
        self.modes = {}
    
    def add_mode(self, name, amps):
        self.modes[name] = {volts: self.volts, amps: amps}
    
    def draw(self, mode, dt_usec):
        mode = self.modes.get(mode, None)
        # @todo: check if mode is not found and throw an error
        success = self.power_source.drain(amps, dt_usec)
        return success  # We might not be able to draw power
        
    
class PowerSource:

    def __init__(self, volts, max_amps):
        self.volts = volts
        self.max_amps = max_amps
        
    def drain(self, amps, dt_usec):
        """
        Drain the appropriate amount of power.
        - For a battery, this would discharge the battery
        - For wall current, this wouldn't likely have an effect
        - Note: we will raise a fault if the drain is more than the ability to supply
        """
        # @todo: Throw a fault if we're drawing too much power? 
        pass

        
    

        
    