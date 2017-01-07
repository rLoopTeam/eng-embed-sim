#!/usr/bin/env python

#!/usr/bin/env python
# coding=UTF-8

# File:     battery.py
# Purpose:  Battery-related classes
# Author:   Ryan Adams (@ninetimeout)
# Date:     2016-Dec-16

# NOTE: Please add your name to 'Author:' if you work on this file. Thanks!

class Brake:
    """
    Model of a single braking unit
    """
    
    def __init__(self):
        self.motor = None  # Should be a model of a motor
        
        # Configuration
        self.negator_torque = 0.7  # Nm -- @todo: move this to config
        
        # Volatile
        self.deployed_pct = 0.0
        
        
    def get_motor_load_torque(self):
        """ Get the torque on the motor from the brakes """
        # Start with the brake lift
        # change to 17deg (tan 17?)
        # change to torque using the pitch of the thread on the ball screw
        # (^ make sure to take friction into account)
        # That should give us the torque acting on the motor. If this torque is greater than the motor max torque, it will slip
        # Take into account that the max holding torque is different from the max torque. How do we know if the motor is holding or moving? 
        # How do we control the stepper motor? Where are the routines for that? 
        
    def step(self, dt_usec):
        """ Calculate our movement this step, and the forces that are acting on us. Notify if, for instance, brake force overcomes motor torque """
        pass
        

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