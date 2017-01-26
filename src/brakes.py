#!/usr/bin/env python
# coding=UTF-8

# File:     brakes.py
# Purpose:  Brakes
# Author:   Ryan Adams (@ninetimeout), Keith Stormo (@kstorminator), Sean (@capsulecorplab)
# Date:     2016-Dec-16

# In A34, drag is for one brake, lift is for both (@kstorminator)

# Holding torque: 2.8Nm
# moving torque is something like 80% of that, depending on step size 1, .5, .25, .125, etc.
# When the controller is trying to change the speed, what does that curve look like? Best torque at about 500rpms.
# We want to deploy in 2 sec -- 5 Revs per second is max when we're facing load -- "strong" speed
# Fine adjustment should be done 
# If we're losing steps (based on MLP, we want to slow down to 3 RPS so we're in maximum torque range)
# @see http://www.orientalmotor.com/technology/articles/article-speed-torque-curves-for-step-motors.html
# ^ has for all stepper motors
#   max speed is 900RPM for any stepper motor, and we only have about 65% of torque (it can go higher, but you only have like 15% of the rated torque)
#   
# If you have 2.8 holding torque, reduce it to 80% if we're running it slow, or down to 65% if we're running as fast as lachlan says 
    # We'll be drawing 5A

# * Make sure that the PID doesn't try to drive the stepper motor faster than it can go -- keep in mind torque!
"""
@see https://rloop.slack.com/archives/eng-numsim/p1484038814001761
@see a34data-ra.xlsx and the grapher output (Ryan's Mac)
F_lift(gap, v) = (3265.1 * e^(-209.4*gap)) * ln(v + 1) - (2636.7 * e^(-207*gap)) * (v + .6) * e ^ (-.16*v)
F_drag(gap, v) = (5632 * e^(-202*gap)) * (-e^(-.3*v) + 1) * (1.5 * e^(-.02*v) + 1)
"""

import numpy as np
import logging

from units import Units
from config import Config

class Brakes(object):
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config  # Note: this is a list of configurations
        
        print "Config: {}".format(self.config)
        
        self._list = []
                
        for i, brake_config in self.config.iteritems():
            self._list.append( Brake(self.sim, Config(brake_config)) )

        # Testing movement

    def __getitem__(self, idx):
        return self._list[idx]

    def __repr__(self):
        return 'Brakes(' + str(self._list) + ')'

    def __str__(self):
        return str(self._list)

    def get_gaps(self):
        # Note: we always only have 2 brakes
        return (self._list[0].gap, self._list[1].gap)

    def step(self, dt_usec):
        for brake in self._list:
            brake.step(dt_usec)

    def close_now(self):
        # Close the brakes NOW (no waiting -- just for simulation testing)
        for brake in self._list:
            brake.gap = brake.minimum_gap
            brake._gap_target = brake.minimum_gap  # TESTING -- the brakes will move back apart if this isn't set. 

    def _move_to_gap_target(self, gap_target):
        for brake in self._list:
            brake._move_to_gap_target(gap_target)

    def get_drag(self, brake_index=None):
        tl_force = 0.0
        
        for brake in self._list:
            tl_force += brake.get_drag()
        
        return tl_force


class MLP:
    """ Linear Positioning Sensor """
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
        
        self.logger = logging.getLogger("MLP")
        
        # Config
        
        # These are the values that the MLP should return at the minimum and maximum physical measurement that you'll be taking 
        # Note that this is akin to what the MLP would read in real life if you were to move your device to the minimum or maximum position and measure the value of the MLP
        # Note that reversed ranges are fine e.g. value_at_min = 100, value_at_max = 19
        # The max and min values are defined in whatever is using the MLP (e.g. the brake system)
        self.value_at_min = self.config.value_at_min
        self.value_at_max = self.config.value_at_max

        # Volatile

    def set_physical_minmax(self, min, max):
        """ Set the range of physical values that should map onto the MLP """
        # This allows you to set the min and the max of the quantity that you want the MLP to measure. 
        # Once you set this, you can pass in a physical number to get_mlp_value() and it will be mapped to an MLP value and returned
        pass
        
        # Maybe we should let the holder of the MLP determine these values and do the mapping? 
        

class Brake:
    """
    Model of a single braking unit
    """
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config

        self.logger = logging.getLogger("Brake")

        # Callbacks (called when gap hits the limits)
        self.retract_sw_callback = None
        self.extend_sw_callback = None

        # Volatile
        #self.gap = Units.SI(self.config.initial_gap)  # @todo: make this work 
        self.gap = Units.SI(self.config.initial_gap)
        self.min_gap = Units.SI(self.config.min_gap)
        self.max_gap = Units.SI(self.config.max_gap)

        # Linear Position Sensor
        # These values will be mapped between min and max gap. Backwards is ok (e.g. 25.4mm -> 2.5mm ==> 3004 -> 298)
        self.mlp_raw_retracted = self.config.mlp_raw_retracted
        self.mlp_raw_extended = self.config.mlp_raw_extended 

        # TESTING ONLY
        self._gap_target = self.gap
        self._gap_close_time = Units.SI(self.config.gap_close_min_time)
        self._gap_close_dist = self.max_gap - self.min_gap
        self._gap_close_speed = self._gap_close_dist / self._gap_close_time  # meters/second -- this is just a guess -- .007 m/s = closing 21mm in 3s
        self.logger.debug("Brake gap close speed: {} m/s".format(self._gap_close_speed))
        # /TESTING
        
        self.deployed_pct = 0.0  # @todo: need to calculate this based on the initial position. Or let this set the initial gap? Probably calculate it from max_gap and 

        self.lift_force = 0.0  # N -- lift against the rail; +lift is away from the rail
        self.drag_force = 0.0  # N -- drag on the pod; -drag is toward the back of the pod

        self.last_lift_force = 0.0
        self.last_drag_force = 0.0

        # Components
        self.motor = None  # Should be a model of a motor?
        
        # Configuration
        self.negator_torque = 0.7  # Nm -- @todo: move this to config
        #self.min_gap = 2.5mm  # ?
        #self.max_gap = 25mm   # ?
        

        # Lead Screw
        # revs per cm=2.5  There are 4 mm per single lead so 2.5 turns move the carriage 1 cm
        # Formulas: http://www.nookindustries.com/LinearLibraryItem/Ballscrew_Torque_Calculations
        self.screw_pitch = .004  # Meters @todo: move to config
        self.drive_efficiency = 0.90  # @todo: to config
        self.backdrive_efficiency = 0.80  # @todo: to config
        
        # Lead Screw Precalculated Values
        self._drive_torque_multiplier = self.screw_pitch / (self.drive_efficiency * 2 * 3.14)
        self._backdrive_torque_multiplier = (self.screw_pitch * self.backdrive_efficiency) / ( 2 * 3.14)
        
        # Motor  @todo: move this to the motor
        # 1.8 deg per full step
        # Step size: .05  # Half steps
        # => 400 steps per revolution at half steps
    
    def set_retract_sw_callback(self, callback):
        self.retract_sw_callback = callback
    
    def set_extend_sw_callback(self, callback):
        self.extend_sw_callback = callback
    
    def get_mlp_value(self):
        """ Use the brake gap and our min/max settings to calculate the raw value for the MLP """
        return np.interp(self.gap, [self.min_gap, self.max_gap], [self.mlp_raw_extended, self.mlp_raw_retracted])

    def _move_to_gap_target(self, gap_target):
        # TESTING ONLY
        self._gap_target = gap_target
    
    def step(self, dt_usec):
        """ Calculate our movement this step, and the forces that are acting on us. Notify if, for instance, brake force overcomes motor torque """
        # Note: doing all these calculations in a single function because function calls are expensive

        self.last_lift_force = self.lift_force
        self.last_drag_force = self.drag_force
        
        v = self.sim.pod.velocity
        
        # TESTING ONLY -- move the gap to the target
        if self.gap > self._gap_target:
            dist = self._gap_close_speed * (dt_usec / 1000000.0)
            self.gap -= dist
        elif self.gap < self._gap_target:
            dist = self._gap_close_speed * (dt_usec / 1000000.0)
            self.gap += dist
        else:
            # Don't really need this, but hey
            self.gap = self._gap_target
        # /TESTING
        
        # Handle the limit switches
        # @todo: Watch out for floating point errors...
        if self.gap <= self.min_gap and self.extend_sw_callback is not None:
            self.extend_sw_callback()
        elif self.gap >= self.max_gap and self.retract_sw_callback is not None:
            self.retract_sw_callback()

        # Force calculations
        gap = self.gap
        
        # Calculate lift (normal force) and drag
        # @see https://rloop.slack.com/archives/eng-numsim/p1484029898001697
        
        F_lift = (3265.1 * np.exp(-209.4*gap)) * np.log(v + 1) - (2636.7 * np.exp(-207*gap)) * (v + .6) * np.exp(-.16*v)  # Newtons, For one brake
        
        # F_drag(gap, v) = (5632 * np.exp(-202*gap)) * (-np.exp(-.3*v) + 1) * (1.5 * np.exp(-.02*v) + 1)  # For both brakes
        F_drag = - (2816 * np.exp(-202*gap)) * (-np.exp(-.3*v) + 1) * (1.5 * np.exp(-.02*v) + 1)  # Newtons, For one brake
        #F_drag = - (5632 * np.exp(-202*gap)) * (-np.exp(-.3*v) + 1) * (1.5 * np.exp(-.02*v) + 1)  # Newtons, For two brakes? @TODO @todo: Confirm brake strength from A34 data!!

        # Save the drag force (to be used by force_brakes.py)
        self.drag_force = F_drag

        # Get linear force acting on lead screw due to the brakes
        # Note: Formula has a 17 degree angle to the rail. Lift force is normal to the rail, drag force is parallel to it. 
        # Force applied to screw is lift*sin(17) + drag*cos(17)
        F_screw = F_lift * 0.292371705 + F_drag * 0.956304756
        #self.logger.debug("Brakes: F_lift = {}; F_drag = {}; F_screw = {}".format(F_lift, F_drag, F_screw))
        
        # Convert linear force to drive torque (motor driven) and backdrive torque (driven by linear force on the screw)
        # Note: Drive torque is the torque required to move the load, and backdrive torque is the torque required for the load to turn the screw on its own
        """
        Should we use back driving torque formuala here? Or torque to lift load? 
        Let's see:
        - the torque exerted on the motor by the brakes is backdriving torque
        - The torque exerted by the negator on the motor is just 0.7Nm
        - The torque exerted by the motor is driving torque (or holding torque? Maybe based on speed of motor? How do we get speed? Calculate # steps over time? Or some other way?)
            - Use raising torque equation if motor is driving in the opposite direction as load torque
            - Use lowering torque eqn if motor is driving in the same direction as load torque
        """
        # Formulas: http://www.nookindustries.com/LinearLibraryItem/Ballscrew_Torque_Calculations
        # Note: Drive and backdrive torques are only used to see if the motor can handle the load
        drive_torque = F_screw * self._drive_torque_multiplier
        backdrive_torque = F_screw * self._backdrive_torque_multiplier
        
        # Negator Torque. Since the negator attempts to drive the screw in the -x direction (which deploys the brakes), we subtract it
        tl_drive_torque = drive_torque - self.negator_torque
        tl_backdrive_torque = backdrive_torque - self.negator_torque
        
        # @todo: add in the mass of the brake (12.3kg) x acceleration -- it's a significant force. Probably should apply to backdrive torque. 
        
        # @todo: determine when to trip the limit switches
        
        #self.logger.debug("Brakes: v={}, Gap={}, F_lift={}, F_drag={}, F_screw={}, dr_tq={}, bd_tq={}".format(v, self.gap, F_lift, F_drag, F_screw, drive_torque, backdrive_torque))
        p = self.sim.pod.position
        a = self.sim.pod.acceleration
        #self.logger.debug("\t".join([str(x) for x in (p, v, a, self.gap, F_lift, F_drag, F_screw, drive_torque, backdrive_torque, tl_drive_torque, tl_backdrive_torque)]))

        # Calculate new gap based on motor / slipping movement
        
    def get_drag(self):
        return self.drag_force  # Negative? 
    
    def get_motor_load_torque(self):
        """ Get the torque on the motor from the brakes """
        # Start with the brake lift
        # change to 17deg (tan 17?)
        # change to torque using the pitch of the thread on the ball screw
        # (^ make sure to take friction into account)
        # That should give us the torque acting on the motor. If this torque is greater than the motor max torque, it will slip
        # Take into account that the max holding torque is different from the max torque. How do we know if the motor is holding or moving? 
        # How do we control the stepper motor? Where are the routines for that? 
        
        

class Motor:
    def __init__(self):
        
        #this is the parameter layout
        #define C_LOCALDEF__LCCM231__M0_MICROSTEP_RESOLUTION__PARAM_INDEX                       (0U)
        #define C_LOCALDEF__LCCM231__M0_MAX_ACCELERATION__PARAM_INDEX                           (1U)
        #define C_LOCALDEF__LCCM231__M0_MICRONS_PER_REVOLUTION__PARAM_INDEX             2U
        #define C_LOCALDEF__LCCM231__M0_STEPS_PER_REVOLUTION__PARAM_INDEX                       3U
        #define C_LOCALDEF__LCCM231__M0_MAX_ANGULAR_VELOCITY__PARAM_INDEX 
        
        # Configuration
        self.max_holding_torque = 2.8 # Nm -- @todo: move this to config
        self.max_drive_torque = 3.5 # Nm -- is this correct? @todo: move this to config
        self.steps_per_revolution = 100      # @todo: get the actual value for this
        self.max_acceleration = None  # @todo: Need to find out what this is
        self.max_angular_velocity = None # @todo: Need to find out what this is
        
        
        # Volatile
        self.max_torque = 0.0  # Nm -- controlled by state machine        
        self.state = "FREE_SPIN"  # {FREE_SPIN, DRIVE, HOLD}

        pass