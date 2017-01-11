#!/usr/bin/env python

from units import Units
import numpy as np

class BrakeForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

    def get_force(self):
        """ Get x force provided by the brakes. """
        # @todo: make this work. Probably need to go through self.sim to get pod velocity, etc. 

        # Numerical simulation run at 6 different velocities -- see Keith's graph 
        # A34 data -- drag is for both brakes, lift is for one brake. Force_y has to do with the difference in force due to magnetic interactions and can be disregarded
        v = self.sim.pod.velocity
        air_gap = .024  # Should be self.sim.pod.brakes.gap, or brakes[i].gap if we're using an array of brakes, which we probably will
        
        # Fdrag(v) = gap_coefficient * (-e^(-.3*v)+1)*(1.5*e^(-.02*v)+1)
        # gap_coefficient = 5632e^-202gap
        
        # @todo: Either the drag force or the lift force is for a single brake, the other is for both. Which is which? 
        gap_coefficient = 5632 * np.exp(-202 * air_gap)
        f_drag = gap_coefficient * (-np.exp(-.3*v) + 1) * (1.5 * np.exp(-.02*v)+1)
        #print "Brake drag at air gap {}: {}".format(air_gap, -f_drag)

        f_drag = self.sim.brake_1.drag_force * 2  # *2 for both brakes. Just testing right now
            
        return (f_drag, 0, 0)

