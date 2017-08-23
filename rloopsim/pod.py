#!/usr/bin/env python
# coding=UTF-8

# File:     pod.py
# Purpose:  Pod-related classes
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2016-Dec-18

# NOTE: Please add your name to 'Author:' if you work on this file. Thanks!

# Note: all units are SI: meters/s^2, meters/s, and meters. Time is in microseconds (?)

from __future__ import division
import logging
import numpy as np
from collections import OrderedDict

# Our stuff
from units import Units
from brakes import *

# Forces
from forces import *


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

        self.name = 'pod_actual'

        self.step_listeners = []
        self.step_forces = OrderedDict()   # This will be filled in during each step

        # Pod physical properties
        # *** NOTE: all distances are in the track/tube reference frame, origin is pod location reference (centerpoint of fwd crossbar).  +x is forward, +y is left, +z is up.
        # @see http://confluence.rloop.org/display/SD/2.+Determine+Pod+Kinematics

        self.mass = Units.SI(self.config.mass)
        self.pusher_plate_offset = Units.SI(self.config.physical.pusher_plate_offset) 
        self.pusher_pin_travel = Units.SI(self.config.physical.pusher_pin_travel)
        
        # Forces that can act on the pod (note: these are cleared at the end of each step)        
        self.net_force = np.array((0.0, 0.0, 0.0))  # Newtons; (x, y, z). +x pushes the pod forward, +z force lifts the pod, y is not currently used. 

        # Initialize actual physical values (volatile variables). All refer to action in the x dimension only. 
        self.acceleration = Units.SI(self.config.acceleration) or 0.0  # meters per second ^2
        self.velocity = Units.SI(self.config.velocity) or 0.0          # meters per second
        self.position = Units.SI(self.config.position) or 0.0          # meters. Position relative to the track; start position is 0m
        
        # @todo: this is just a sketch, for use with the hover engine calculations. Maybe switch accel, velocity, and position to coordinates? hmmmm...
        self.z_acceleration = 0.0
        self.z_velocity = 0.0
        self.he_height = Units.SI(self.config.landing_gear.initial_height)  # This should be gotten from the starting height of the lift mechanism
        self._initial_he_height = self.he_height  # @todo: Remove this -- it's only used as a temporary block from going through the floor until the landing gear is implemented
        
        self.elapsed_time_usec = 0

        # Values from the previous step (for lerping and whatnot)
        self.last_acceleration = 0.0
        self.last_velocity = 0.0
        self.last_position = 0.0
        self.last_he_height = 0.0

        # Handle forces that act on the pod
        """
        self.forces = []
        self.forces.append( AeroForce(self.sim, self.config.forces.aero) )
        self.forces.append( BrakeForce(self.sim, self.config.forces.brakes) )
        self.forces.append( GimbalForce(self.sim, self.config.forces.gimbals) )
        self.forces.append( HoverEngineForce(self.sim, self.config.forces.hover_engines) )
        self.forces.append( LateralStabilityForce(self.sim, self.config.forces.lateral_stability) )
        self.forces.append( LandingGearForce(self.sim, self.config.forces.landing_gear) )
        """
        self.force_exerters = OrderedDict()
        self.force_exerters['aero'] = AeroForce(self.sim, self.config.forces.aero)
        self.force_exerters['brakes'] = BrakeForce(self.sim, self.config.forces.brakes) 
        self.force_exerters['gimbals'] = GimbalForce(self.sim, self.config.forces.gimbals)
        self.force_exerters['hover_engines'] = HoverEngineForce(self.sim, self.config.forces.hover_engines)
        self.force_exerters['lateral_stability'] = LateralStabilityForce(self.sim, self.config.forces.lateral_stability)
        self.force_exerters['landing_gear'] = LandingGearForce(self.sim, self.config.forces.landing_gear)
        
        # Forces applied during the step (for recording purposes)
        # @todo: Maybe initialize these to ForceExerter.data(0,0,0)?
        self.step_forces = OrderedDict()
        self.step_forces['aero'] = ForceExerter.data(0,0,0)
        self.step_forces['brakes'] = ForceExerter.data(0,0,0)
        self.step_forces['gimbals'] = ForceExerter.data(0,0,0)
        self.step_forces['hover_engines'] = ForceExerter.data(0,0,0)
        self.step_forces['lateral_stability'] = ForceExerter.data(0,0,0)
        self.step_forces['landing_gear'] = ForceExerter.data(0,0,0)

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
        
        #self.brakes = []
        #for brake_config in self.config.brakes:
        #    self.brakes.append(Brake(self.sim, brake_config))
        self.brakes = Brakes(self.sim, self.config.brakes)
        
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
    
    def add_step_listener(self, listener):
        """ 
        Register a listener that will be called every step. 
        A step listener can be any class that implements the following method:
        - step_callback(self, sensor, times, samples)
        """
        self.step_listeners.append(listener)

    def apply_forces(self):        
        """ Apply all forces provided by the exerters, in order. This happens every step, and all forces are then cleared for the next step. """
        """
        for exerter in self.forces:
            self.apply_force(exerter.get_force())
        """
        for key, exerter in self.force_exerters.iteritems():
            force = exerter.get_force()
            self.step_forces[key] = force
            self.apply_force(force)
        
    def apply_force(self, force):
        """ Apply force to the pod in the x direction. Note the forces are cleared after each step() """
        self.net_force += np.array((force.x, force.y, force.z))  # np.array() because forces are (x,y,z)
        #self.logger.debug("Force {} applied (total force is {})".format(force, self.net_force))
    
    def get_csv_row(self):
        out = []
        
        out.append(self.elapsed_time_usec)
        out.append(self.net_force)
        out.append(self.acceleration)
        out.append(self.velocity)
        out.append(self.position)
        
        return ",".join([str(x) for x in out])
            
    def get_accel(self):
        # If the pusher is connected, get accel from the pusher
        # If not, get it from the net force. Must call apply forces before this.
        # Actually, if the pusher is in the process of disconnecting, don't get it from the pusher
            # If the deceleration of the pod is less than that of the pusher, use the pod forces
            # Also need to determine by position of the pusher and pod whether the pusher is engaged
            # use pod.physical.pusher_plate_offset (use that as start position for the pusher)
            # Note: probably need a disengage distance for when the pin switches disengage
        pass  # @todo: delete this method; maybe keep the notes

    # -------------------------
    # Simulation methods
    # -------------------------

    def update_physics(self, dt_usec):
        """ Step the physics of the pod (forces, a/v/p, etc.) """
        
        # Save off our current values
        self.last_acceleration = self.acceleration
        self.last_velocity = self.velocity
        self.last_position = self.position
        self.last_he_height = self.he_height
        self.last_z_velocity = self.z_velocity

        # -------------------
        # X physics
        # -------------------
        
        # Calculate the pod's natural accel (decel) based on outside forces (except for the pusher)
        # F = ma, a = F/m
        pod_natural_accel = self.net_force[0] / self.mass
        
        # If the pusher is in contact, we may want to use the pusher's acceleration as our own
        if self.pusher_in_contact():
            # If the pusher's acceleration > ours, use its accel directly
            # instead of our forces to calculate our acceleration
            if self.sim.pusher.acceleration > pod_natural_accel:
                self.acceleration = self.sim.pusher.acceleration
            else:
                # Pusher is pulling back from the pod; use our own decel
                self.acceleration = pod_natural_accel
        else:
            # Pusher is not in contact
            self.acceleration = pod_natural_accel

        
        t_sec = dt_usec / 1000000.0
        
        # v*t + 1/2*a*t^2
        self.position += self.velocity * t_sec + 0.5 * self.acceleration * (t_sec ** 2)
        
        # vf = v0 + at
        self.velocity = self.velocity + self.acceleration * t_sec

        # @todo: change this to log to a data stream or file? 
        #self.logger.info(self.get_csv_row())  # @todo: change this to a listener


        # -------------------
        # Z physics
        # -------------------
        
        # Subtract gravity: F = mg
        self.net_force[2] += -9.80665 * self.mass

        # Calculate z acceleration, velocity, and height for this step. 
        self.z_acceleration = self.net_force[2] / self.mass
        self.z_velocity = self.z_acceleration * t_sec  # Note: we're considering momentum to be negligible here, so no velocity addition here
        self.he_height += (self.z_velocity * t_sec + 0.5 * self.z_acceleration * (t_sec ** 2)) / 2
        
        # @todo: make this work
        #if self.he_height < self.landing_gear.he_height:
        #    self.he_height = self.landing_gear.he_height
        if self.he_height < self._initial_he_height:  # @todo: remove this in favor of getting the actual height of the landing gear
            self.he_height = self._initial_he_height

        #print "Net z force: {}, accel {}, velocity {}, he_height {}".format(self.net_force[2], self.z_acceleration, self.z_velocity, self.he_height)
        #print self.he_height

        # Update time
        self.elapsed_time_usec += dt_usec

        # Clear forces for the next step
        self.net_force = np.array((0.0, 0.0, 0.0))  # x, y, z

    def step(self, dt_usec):
        #self.step_physics(dt_usec)
        #self.step_sensors(dt_usec)
        #self.step_controls(dt_usec)
        
        # Apply forces
        self.apply_forces()  # @todo: make this work
        
        # Update physics
        self.update_physics(dt_usec)
                
        # Update our components (@todo: move this up?)
        self.brakes.step(dt_usec)
        
        # Do other things? Update sensors? 
        for step_listener in self.step_listeners:
            step_listener.step_callback(self, None)
    
    # -------------------------
    # Physical methods
    # -------------------------

    def pusher_in_contact(self):
        """ Is the pusher in contact with the pod (calculated by relative distance)? """
        return self.sim.pusher.position >= self.position + self.pusher_plate_offset

    def pusher_pin_engaged(self):
        # Determine if the pusher pin is engaged based on relative distance
        return self.sim.pusher.position + self.pusher_pin_travel >= self.position + self.pusher_plate_offset

    # -------------------------
    # State machine helpers
    # -------------------------

    def state_BRAKE(self):
        pass