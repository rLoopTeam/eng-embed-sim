#!/usr/bin/env python

from units import Units

class BrakeForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

    def get_force(self):
        """ Get x force provided by the brakes. """
        # @todo: make this work. Probably need to go through self.sim to get pod velocity, etc. 
        return 0.0
        
    def get_lift(self):
        """ 
        Get lift provided by the brakes. Note that this is NOT 'lift' 
        against the rail, but refers to horizontal lift. This will
        will probably remain 0.0. 
        """
        return 0.0