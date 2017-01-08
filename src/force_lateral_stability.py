#!/usr/bin/env python

from units import Units

class LateralStabilityForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

        self.damping_coefficient = Units.SI(self.config.damping_coefficient)

    def get_force(self):
        """ Get x force (drag -- return a negative number) provided by the lateral stability wheels. """
        # Note: You can get pod velocity/acceleration/position using e.g. self.sim.pod.velocity (see pod.py __init__() for vars)
        x = - ( self.damping_coefficient * self.sim.pod.velocity)
        y = 0 # No y force
        z = 0 # No z force
        return (x, y, z)