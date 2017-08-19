#!/usr/bin/env python

from collections import namedtuple

class Sensor:
    def __init__(self):
        pass
        
        self.data = namedtuple('SensorData', ['t_usec', 'value'])
        
        self.step_listeners = []
        
        
        
    def get_step_samples(self):
        pass
        
    def step(self, dt_usec):
        
        