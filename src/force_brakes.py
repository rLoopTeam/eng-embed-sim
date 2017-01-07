#!/usr/bin/env python

from units import Units

class BrakeForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

    def get_force(self):
        """ Get x force provided by the brakes. """
        # @todo: make this work. Probably need to go through self.sim to get pod velocity, etc. 

        # Numerical simulation run at 6 different velocities -- see Keith's graph 
        # A34 data -- drag is for both brakes, lift is for one brake. Force_y has to do with the difference in force due to magnetic interactions and can be disregarded
        velocity = 0
        air_gap = 0
            
        return (0, 0, 0)

