#!/usr/bin/env python

from units import Units

class LateralStabilityForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

    def get_force(self):
        """ Get x force (drag -- return a negative number) provided by the lateral stability wheels. """
        # Note: You can get pod velocity/acceleration/position using e.g. self.sim.pod.velocity (see pod.py __init__() for vars)
        return (0,0,0)
