#!/usr/bin/env python

from units import Units

class LandingGearForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

    def get_force(self):
        """ Get the drag force (-x) provided by the landing gear"""
        # @todo: Probably need to check the state of the landing gear for this (e.g. are they on the track?).
        # Note: you can get the state of the landing gear by going through self.sim 
        return 0.0
        
    def get_lift(self):
        """ 
        Get lift provided by landing gear. Note that the landing gear 
        does not provide lift, but may directly affect the height of 
        the pod (handled elsewhere) 
        """
        return 0.0