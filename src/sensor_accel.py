#!/usr/bin/env python

import numpy as np
import logging 
from collections import namedtuple
from operator import attrgetter  # For sorting named tuples

from sensors import PollingSensor    
    
class Accelerometer(PollingSensor):

    def __init__(self, sim, config):
        PollingSensor.__init__(self, sim, config)
        self.logger = logging.getLogger("LaserContrastSensor")
        
        self.data = namedtuple('AccelerometerData', ['t', 'x', 'y', 'z'])
        
    def create_step_samples(self, dt_usec):
        
        # Pod acceleration (x)
        pod_start_accel = self.sim.pod.last_acceleration
        pod_end_accel = self.sim.pod.acceleration
        
        # Create the samples (lerp between the times)
        sample_data = self._lerp(pod_start_accel, pod_end_accel)
        sample_times = sample_times = self._get_sample_times(dt_usec)

        # @todo: apply a rotation matrix to simulate the actual 
        return [self.data(t, sample_data[i], 0, 0) for i, t in enumerate(sample_times)]
        
        
class AccelerometerTestListener(object):
    def __init__(self, sim, config=None):
        self.sim = sim
        self.config = config
        
    def step_callback(self, sensor, samples):
        for sample in samples:
            print "AccelerometerSensor sample: {}".format(sample)