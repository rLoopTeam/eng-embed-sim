#!/usr/bin/env python

from units import Units

class AeroForce:
    """ Applies """
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config  # Note: this is passed in, and is located at sim.pod.forces.aero in the config file
        
        # @see http://www.softschools.com/formulas/physics/air_resistance_formula/85/
        self.air_resistance_k = Units.SI(self.config.air_density) * self.config.drag_coefficient * Units.SI(self.config.drag_area) / 2
        
    def get_force(self):
        """ Get the drag force (based on pod velocity, negative in the x direction since it's drag) """
        return -self.air_resistance_k * self.sim.pod.velocity ** 2
    
    def get_lift(self):
        """ Get lift provided by this force provider (none in this case) """
        return 0.0