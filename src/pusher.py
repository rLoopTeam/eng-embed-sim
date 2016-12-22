#!/usr/bin/env python
# coding=UTF-8

# File:     pusher.py
# Purpose:  Pusher-related classes and time/acceleration/speed/position info
# Author:   Ryan Adams (@ninetimeout)
# Date:     2016-Dec-17

# NOTE: Please add your name to 'Author:' if you work on this file. Thanks!

# Note: all units are SI: meters/s^2, meters/s, and meters. Time is in microseconds (?)

from __future__ import division

class Pusher:
    
    def __init__(self, position=0):

        # Actual position (volatile variables) - pod reference frame
        self.acceleration = 0             # meters per second ^2
        self.velocity = 0                 # meters per second
        self.position = position          # meters
                
        # State Machine (HOLD, PUSH, COAST, BRAKE)
        self.state = 'HOLD'
        self.coast_timer = 0
        
        # Configuration (these are defaults -- you can also set these directly at some later point)
        self.push_accel = 9.8             # meters per second ^2
        self.max_velocity = 150.0         # meters per second
        self.coast_time_usec = 2000000    # microseconds
        self.brake_accel = -14.7          # meters per second ^2
        
    def update_physical(self, dt_usec):
        """ Update position and velocity based on current acceleration """
        
        t_sec = dt_usec / 1000000
        
        # v*t + 1/2*a*t^2
        self.position += self.velocity * t_sec + 0.5 * self.acceleration * t_sec * t_sec
        
        # vf = v0 + at
        self.velocity = self.velocity + self.acceleration * t_sec

    def update_sensors(self, dt_usec):
        """ Update sensor values """
        pass  # nothing to do for the pusher


    # -------------------------
    # Simulation methods
    # -------------------------

    def step(self, dt_usec):
        """ Handle the pusher state machine and simulation interactions """

        if self.state == "HOLD":
            pass
        elif self.state == "PUSH":
            if self.velocity < self.max_velocity:
                self.acceleration = self.push_accel
            else:
                self.acceleration = 0.0
                self.state = "COAST"
        elif self.state == "COAST":
            if self.coast_timer > self.coast_time_usec:
                self.state = "BRAKE"
                self.coast_timer = 0
            else:
                self.coast_timer += dt_usec
        elif self.state == "BRAKE":
            if self.velocity >= 0.0:
                self.acceleration = self.brake_accel
            else:
                self.acceleration = 0.0
                self.velocity = 0.0  # In case we overshot due to resolution
                self.state = "HOLD"
        else:
            raise Exception("Unknown state {}".format(self.state))
                
        self.update_physical(dt_usec)
        self.update_sensors(dt_usec)   # Doesn't do anything, just here as an example


    # -------------------------
    # Control hooks
    # -------------------------
    
    def start_push(self):
        self.state = "PUSH"
    

if __name__ == "__main__":

    import argparse
    import datetime
    
    # Command line parsing
    parser = argparse.ArgumentParser(description="Battery class and drain simulation utility")
    parser.add_argument('-s', '--fixed_timestep_usec', help="Timestep of the simulation in microseconds", default=100000, required=False)
    parser.add_argument('-p', '--position', help="Initial position in meters", default=0, required=False)

    parser.add_argument('-a', '--acceleration', help="Acceleration during push in m/s^2 (e.g. 9.8 = 1G)", default=9.8, required=False)
    parser.add_argument('-c', '--coast', help="Coast time in microseconds", default=1000000, required=False)
    parser.add_argument('-b', '--brake', help="Acceleration during braking in m/s^2 (e.g. -14.7 = 1.5G)", default=-14.7, required=False)
    parser.add_argument('-m', '--max_v', help="Maximum push velocity in m/s", default=150, required=False)
    # @todo: For testing purposes only -- change over to generate as many as needed based on conditions if not provided
    parser.add_argument('-n', '--n_records', help="Number of records to generate", default=1001, required=False)
    args = parser.parse_args()
    
    # Pusher setup
    pusher = Pusher(float(args.position))
    
    pusher.push_accel = float(args.acceleration)
    pusher.coast_time_usec = float(args.coast)
    pusher.brake_accel = float(args.brake)
    pusher.max_velocity = float(args.max_v)

    # Simulation settings
    fixed_timestep_usec = int(args.fixed_timestep_usec)
    
    # Start pushing right at the beginning. Could set up a wait before it, but not right now
    pusher.start_push()
    
    # test simulation -- Does a push/coast/brake cycle 
    print "{},{},{},{},{}".format("t_usec","acceleration","velocity","position","processing_usec") # Header
    for i in xrange(int(args.n_records)):
        t = i * fixed_timestep_usec  # Note: need to offset -- what we're printing is *after* the step
        start = datetime.datetime.now()
        duration_usec = datetime.datetime.now() - start
        print "{},{},{},{},{}".format(t, pusher.acceleration, pusher.velocity, pusher.position, duration_usec.microseconds)        
        pusher.step(fixed_timestep_usec)
