#!/usr/bin/env python

from units import Units

class LateralStabilityForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 
        
        self.name = "F_lateral_stability"
        self.step_listeners = []
        self.data = namedtuple(self.name, ['x', 'y', 'z'])
        
        self.damping_coefficient = Units.SI(self.config.damping_coefficient)

    def get_force(self):
        """ Get x force (drag -- return a negative number) provided by the lateral stability wheels. """
        # Note: You can get pod velocity/acceleration/position using e.g. self.sim.pod.velocity (see pod.py __init__() for vars)
        x = - ( self.damping_coefficient * self.sim.pod.velocity )
        y = 0 # No y force
        z = 0 # No z force
        return self.data((x, y, z))
        
    def add_step_listener(self, listener):
        self.step_listeners.append(listener)

    def step(self, dt_usec):
        """ Apply the force to the pod """
        force = self.get_force()
        self.pod.apply_force(force)
        for step_listener in self.step_listeners:
            step_listener.step_callback(self, [force])