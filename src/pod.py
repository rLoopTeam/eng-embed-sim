#!/usr/bin/env python
# coding=UTF-8

# File:     pod.py
# Purpose:  Pod-related classes
# Author:   Ryan Adams (@ninetimeout)
# Date:     2016-Dec-18

# NOTE: Please add your name to 'Author:' if you work on this file. Thanks!

# Note: all units are SI: meters/s^2, meters/s, and meters. Time is in microseconds (?)

from __future__ import division
import logging
from units import Units
from brakes import *

class PodComponent:
    def __init__(self, name, type, location, sim_obj):
        self.name = name
        self.type = component_type
        self.pod_location_ref = None  # A vector from the physical location of the component to the pod reference point. In this sim, probably just the x component of that vector
        self.sim_obj = sim_obj  # A steppable object (e.g. sensor, actuator, physical component)
        

class Pod:
    
    def __init__(self, sim, config):

        self.logger = logging.getLogger("Pod")
        self.logger.info("Initializing pod")

        self.sim = sim
        self.config = config

        # Pod physical properties
        # *** NOTE: all distances are in the tube reference frame, origin is pod location reference (centerpoint of fwd crossbar).  +x is forward, +y is left, +z is up.
        # @see http://confluence.rloop.org/display/SD/2.+Determine+Pod+Kinematics

        self.mass = Units.SI(self.config.mass)
        print "Config mass: " + str(self.config.mass)

        # Forces that can act on the pod (note: these are cleared at the end of each step)        
        self.net_force = 0  # This will change, and may affect acceleration

        # Actual physical values (volatile variables). All refer to action in the x dimension only. 
        self.acceleration = 0.0      # meters per second ^2
        self.velocity = 0.0          # meters per second
        self.position = 0.0          # meters. Position relative to the tube; start position is 0m
        
        self.elapsed_time_usec = 0
        
        # Pre-calculated values
        
        # @see http://www.softschools.com/formulas/physics/air_resistance_formula/85/
        self.air_resistance_k = Units.SI(self.config.air_density) * self.config.drag_coefficient * Units.SI(self.config.drag_area) / 2

        
        """ Sketch:
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
        """


    def apply_force(self, force):
        """ Apply force to the pod in the x direction. Note the forces are cleared after each step() """
        self.net_force += force
        self.logger.debug("Force {} applied (total force is {})".format(force, self.net_force))


    def get_aero_drag(self):
        """ Calculate the drag on the pod due to air (return a negative force) """
        # @todo: use speed and tube pressure to get the aero drag. Return a negative force (-x)
        return -self.air_resistance_k * self.velocity ** 2

    def get_brake_drag(self):
        """ Calculate the drag on the pod contributed by the brakes (return a negative force) """
        pass

    def get_hover_engine_drag(self):
        """ Calculate the drag on the pod contributed by the hover engines (return a negative force)"""
        pass

    def get_gimballing_force(self):
        """ Get the positive or negative force contributed by the current gimbaling of the engines """
        pass
    
    def get_csv_row(self):
        out = []
        
        out.append(self.elapsed_time_usec)
        out.append(self.net_force)
        out.append(self.acceleration)
        out.append(self.velocity)
        out.append(self.position)
        
        return ",".join([str(x) for x in out])
            
    def apply_forces(self):        
        self.apply_force(self.get_aero_drag())
        #self.apply_force(self.get_brake_drag())
        #self.apply_force(self.get_hover_engine_drag())
        #self.apply_force(self.get_gimballing_force())

    
    # -------------------------
    # Simulation methods
    # -------------------------

    def update_physics(self, dt_usec):
        """ Step the physics of the pod (forces, a/v/p, etc.) """
        # F = ma, a = F/m
        self.acceleration = self.net_force / self.mass
        
        t_sec = dt_usec / 1000000
        
        # v*t + 1/2*a*t^2
        self.position += self.velocity * t_sec + 0.5 * self.acceleration * (t_sec ** 2)
        
        # vf = v0 + at
        self.velocity = self.velocity + self.acceleration * t_sec

        # @todo: change this to log to a data stream or file? 
        self.logger.info(self.get_csv_row())

        # Update time
        self.elapsed_time_usec += dt_usec

        # Clear forces for the next step
        self.net_force = 0

    def step(self, dt_usec):
        #self.step_physics(dt_usec)
        #self.step_sensors(dt_usec)
        #self.step_controls(dt_usec)
        
        # Apply forces
        self.apply_forces()  # @todo: make this work
        
        # Update physics
        self.update_physics(dt_usec)
        
        # Do other things? Update sensors? 
        
    
    # -------------------------
    # Physical methods
    # -------------------------
    def connect_pusher(self, pusher):
        """ Update internal state to reflect that the pusher is connected """
        # @todo: make this work
        self.pusher = pusher
        # @todo: set internal flags that emulate the physical and electronic brake lockout
        pass
    
    def disconnect_pusher(self):
        """ Update the internal state to reflect a disconnection of the pusher """
        # @todo: make this work
        pass
    

    # -------------------------
    # State machine helpers
    # -------------------------

    def state_BRAKE(self):
        pass