#!/usr/bin/env python

from units import Units

class GimbalForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

        self.name = "F_gimbals"
        self.step_listeners = []

    def get_force(self):
        """ Get x force provided by the hover engines. Note that this does NOT include force provided by gimbaling. """
        # @todo: decide whether or not we want to have gimbaling provide x force and lift for 4 of the engines, or to do x force (drag) for all engines in force_hover_engines.py
        return (0,0,0)
        
    def add_step_listener(self, listener):
        self.step_listeners.append(listener)

    def step(self, dt_usec):
        """ Apply the force to the pod """
        force = self.get_force()
        self.pod.apply_force(force)
        for step_listener in self.step_listeners:
            step_listener.callback(self, [force])