#!/usr/bin/env python
# coding=UTF-8

# File:     pod.py
# Purpose:  Pod-related classes
# Author:   Ryan Adams (@ninetimeout)
# Date:     2016-Dec-18

# NOTE: Please add your name to 'Author:' if you work on this file. Thanks!

# Note: all units are SI: meters/s^2, meters/s, and meters. Time is in microseconds (?)

from __future__ import division

from brakes import *

class Pod:
    
    def __init__(self, acceleration=0, velocity=0, position=0):

        # Actual physical values (volatile variables)
        self.acceleration = acceleration  # meters per second ^2
        self.velocity = velocity          # meters per second
        self.position = position          # meters

        # Pod components
        self.fcu = FcuModel()

        # @todo: Should these just be class members? Why put them in a dict? Should we have a 'sensors' list so we can loop over them for, e.g. output csv?
        self.laser_height_sensors = {
            'laser_l': LaserHeightSensor(self),
            'laser_r': LaserHeightSensor(self),
            'laser_aft_yaw': LaserHeightSensor(self)
        }

        # @todo: this is just a sketch to see interfaces. Do not use as-is
        # Brakes need to know about the FCU and the battery (?)
        self.brakes = {
            'brake_l': BrakeModel(self),
            'brake_r': BrakeModel(self)
        }
    

    # -------------------------
    # Simulation methods
    # -------------------------

    def update(self, dt_usec):
        pass

    def step(self, dt_usec):
        pass
        
        
    # -------------------------
    # State machine helpers
    # -------------------------

    def state_BRAKE(self):
        pass