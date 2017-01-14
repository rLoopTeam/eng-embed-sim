#!/usr/bin/env python

from units import Units

class LandingGearForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

        self.name = "F_landing_gear"
        self.step_listeners = []

    def get_force(self):
        """ Get the drag force (-x) provided by the landing gear"""
        # @todo: Probably need to check the state of the landing gear for this (e.g. are they on the track?).
        # Note: you can get the state of the landing gear by going through self.sim 

        """ 
        Note that the landing gear does not provide lift, but may 
        directly affect the height of the pod (handled elsewhere) 
        """
        return (0,0,0)
        
    def add_step_listener(self, listener):
        self.step_listeners.append(listener)

    def step(self, dt_usec):
        """ Apply the force to the pod """
        force = self.get_force()
        self.pod.apply_force(force)
        for step_listener in self.step_listeners:
            step_listener.callback(self, [force])