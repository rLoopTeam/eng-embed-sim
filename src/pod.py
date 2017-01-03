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

# Forces
from force_aero import AeroForce
from force_brakes import BrakeForce
from force_gimbals import GimbalForce
from force_hover_engines import HoverEngineForce
from force_landing_gear import LandingGearForce
from force_lateral_stability import LateralStabilityForce


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
        self.net_force = 0.0  # Newtons, in the x direction This will change, and may affect acceleration
        self.net_lift = 0.0

        # Actual physical values (volatile variables). All refer to action in the x dimension only. 
        self.acceleration = 0.0      # meters per second ^2
        self.velocity = 0.0          # meters per second
        self.position = 0.0          # meters. Position relative to the tube; start position is 0m
        
        self.height = 0.0  # Probably need to set this with the config (starting height? What about the landing gear? )

        self.elapsed_time_usec = 0

        # Values from the previous step (for lerping and whatnot)
        self.last_acceleration = 0.0
        self.last_velocity = 0.0
        self.last_position = 0.0
        self.last_height = 0.0


        # Handle forces that act on the pod
        self.forces = []
        self.forces.append( AeroForce(self.sim, self.config.forces.aero) )
        self.forces.append( BrakeForce(self.sim, self.config.forces.brakes) )
        self.forces.append( GimbalForce(self.sim, self.config.forces.gimbals) )
        self.forces.append( HoverEngineForce(self.sim, self.config.forces.hover_engines) )
        self.forces.append( LateralStabilityForce(self.sim, self.config.forces.lateral_stability) )
        self.forces.append( LandingGearForce(self.sim, self.config.forces.landing_gear) )

        # Pre-calculated values
        
        # HE Drag
        """
        Drag for a single hover engine (keep in mind that we have 8):
        
        Constants:
        w: Comes from solving 3d maxwell's equations (@whiplash) and using other fancy math -- provided by @whiplash -- not dependent on velocity, just depends on magnetic characteristics
        mu_0: Absolute permeability of the vacuum (constant) -- permeability constant, magnetic constant, etc. -- permeability of free space
        m: Magnetic dipole strength (constant, but depends on how magnets are arranged)
        h: thickness of conducting material (rail in this case)
        rho: density of conducting material (aluminum in this case)

        Variables: 
        z_0: Distance between magnet and conducting surface
        v: Velocity
        
        Calculated:        
        w = 2 * rho / (mu_0 * h)
        F_lift / F_drag = v / w
        F_lift = ((3 * mu_0 * m**2) / (32 * 3.14159 * z_0**4)) * (1 - w * (v**2 + w**2)**(-1/2))

        Values (from @whiplash): 
        mu_0: 4 pi x10e-7
        rho: 2.7 g/cubic centimeter
        h: 0.5 in
        m: (@whiplash will need to calculate this -- it's a vector quantity, need to draw a magnetic circuit) 
        """
        
        # Brakes
        # ?

        
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
        #self.logger.debug("Force {} applied (total force is {})".format(force, self.net_force))

    def apply_lift(self, lift_force):
        self.net_lift += lift_force
        #if lift_force != 0:
        #    self.logger.debug("Lift {} applied (total lift is {})".format(force, self.net_force))
    
    def get_csv_row(self):
        out = []
        
        out.append(self.elapsed_time_usec)
        out.append(self.net_force)
        out.append(self.acceleration)
        out.append(self.velocity)
        out.append(self.position)
        
        return ",".join([str(x) for x in out])
            
    def apply_forces(self):        
        """ Apply all forces provided by the exerters, in order. This happens every step, and all forces are then cleared for the next step. """
        for exerter in self.forces:
            self.apply_force(exerter.get_force())
            self.apply_lift(exerter.get_lift())
    
    
    # -------------------------
    # Simulation methods
    # -------------------------

    def update_physics(self, dt_usec):
        """ Step the physics of the pod (forces, a/v/p, etc.) """
        
        # Save off our current values
        self.last_acceleration = self.acceleration
        self.last_velocity = self.velocity
        self.last_position = self.position

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