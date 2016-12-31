#!/usr/bin/env python

from units import Units

class LateralStabilityForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

    def get_force(self):
        """ Get x force (drag -- return a negative number) provided by the lateral stability wheels. """
        # @todo: decide whether or not we want to have gimbaling provide x force and lift for 4 of the engines, or to do x force (drag) for all engines here...
        return 0.0
        
    def get_lift(self):
        """ Get lift provided by the lateral stability wheels (probably none) """
        return 0.0