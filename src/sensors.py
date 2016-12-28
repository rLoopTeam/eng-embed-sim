#!/usr/bin/env python

#!/usr/bin/env python
# coding=UTF-8

# File:     sensors.py
# Purpose:  Sensor classes
# Author:   Ryan Adams (@ninetimeout)
# Date:     2016-Dec-17

# NOTE: Please add your name to 'Author:' if you work on this file. Thanks!

# Note: all units are SI: meters/s^2, meters/s, and meters. Time is in microseconds (?)

from collections import deque

class BaseSensor:
    """ Base sensor class. """
    
    """
    Note: Sensors will need inputs from the outside world -- sensors will need to 'sample' the world. 
          - How do we connect a sensor to what it needs to measure? In the constructor? 
          - Probably want an id as well for logging purposes.
    
    
    """

    def __init__(self):

        # Sensor value access
        self.fifo = deque()
        
        # Configuration
        self.sampling_rate_hz = 0

        # Internal handling
        self.__sample_overflow = 0.0
    
    def create_sample(self):
        """ Create a single measurement and return it. """
        pass
    
    def step(self, dt_usec):
        """ Fill the queue with values based on the amount of time that's passed """
        # Add samples to the buffer based on how much time has passed and our sampling rate
        n_samples = self.__sample_overflow + self.sampling_rate_hz * dt_usec / 1000000.0
        self.__sample_overflow = n_samples - int(n_samples)  # Save off the remainder
        n_samples = int(n_samples)  # Discard the remainder
                
        for i in xrange(n_samples):
            self.fifo.appendleft(self.create_sample())        


import random

class LaserDistanceSensor(BaseSensor):
    
    def create_sample(self):
        # @todo: fix this up
        return 18.3 + random.random() * 0.01
                
        
class Accelerometer:
    
    def __init__(self, pod):
        self.pod = pod

        # Volatile
        self.fifo = deque()
        self.sample_overflow = 0.  # Our timestep won't always yield a clean number (e.g. 'we should take 8.6 samples for this dt_usec'. Store the remainder here.)
        
        # Configuration
        self.sampling_rate_hz = 800
        self.buffer_size = 32
        self.precision = 14
        self.buffer_mode = "something"   # Circular? 
    
    def step(self, dt_usec):
        # Add samples to the buffer based on how much time has passed and our sampling rate
        n_samples = self.sample_overflow + self.sampling_rate_hz * dt_usec / 1000000.0
        self.sample_overflow = n_samples - int(n_samples)  # Save off the remainder
        n_samples = int(n_samples)  # Discard the remainder
        
        for i in xrange(n_samples):
            self.fifo.pushleft(self.create_sample())
        
    def create_sample(self):
        pass
        # sample = self.pod.acceleration + fuzzing?
        # return (x, y, z)
        
        
if __name__ == "__main__":
    
    dt_usec = 100002
    sensor = LaserDistanceSensor()
    sensor.sampling_rate_hz = 200
    for i in xrange(10):
        sensor.step(dt_usec)
        print len(sensor.fifo)
    