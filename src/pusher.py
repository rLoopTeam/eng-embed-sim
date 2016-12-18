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
    
    def __init__(self, acceleration=0, velocity=0, position=0):
        self.acceleration = acceleration  # meters per second ^2
        self.velocity = velocity          # meters per second
        self.position = position          # meters
        
        print self.__dict__
        
    def push(self, acceleration, dt_usec):
        self.acceleration = acceleration
        t_sec = dt_usec / 1000000
        
        # v*t + 1/2*a*t^2
        self.position += self.velocity * t_sec + 0.5 * self.acceleration * t_sec * t_sec
        
        # vf = v0 + at
        self.velocity = self.velocity + self.acceleration * t_sec

    def coast(self, dt_usec):
        self.acceleration = 0
        # Not much else to do
        
    def brake(self, acceleration, dt_usec):
        # We'll just use a negative 'push'
        self.push(acceleration, dt_usec)

    def step(self, dt_usec):
        """ Handle the pusher state machine and simulation interactions """
        pass


if __name__ == "__main__":

    import argparse
    import datetime
    
    parser = argparse.ArgumentParser(description="Battery class and drain simulation utility")
    parser.add_argument('-s', '--fixed_timestep_usec', help="Timestep of the simulation in microseconds", default=500000, required=False)
    parser.add_argument('-a', '--acceleration', help="Acceleration in m/s^2", default=0, required=False)
    parser.add_argument('-v', '--velocity', help="Initial velocity in m/s", default=0, required=False)
    parser.add_argument('-p', '--position', help="Initial position in meters", default=0, required=False)
    
    # For testing purposes only -- change over to generate as many as needed based on conditions
    parser.add_argument('-n', '--n_records', help="Number of records to generate", default=1001, required=False)

    args = parser.parse_args()
    pusher = Pusher(args.acceleration, args.velocity, args.position)

    # Simulation settings
    fixed_timestep_usec = int(args.fixed_timestep_usec)
    
    # test simulation -- just outputs a constant acceleration of 1g
    print "{},{},{},{},{}".format("t_usec","acceleration","velocity","position","processing_usec") # Header
    for i in xrange(int(args.n_records)):
        t = i * fixed_timestep_usec  # Note: need to offset -- what we're printing is *after* the step
        start = datetime.datetime.now()
        duration_usec = datetime.datetime.now() - start
        print "{},{},{},{},{}".format(t, pusher.acceleration, pusher.velocity, pusher.position, duration_usec.microseconds)        
        pusher.push(9.8, fixed_timestep_usec)
