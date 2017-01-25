#!/usr/bin/env python

import numpy as np
import logging 
from collections import namedtuple
from operator import attrgetter  # For sorting named tuples

from sensors import PollingSensor    
    
class Accelerometer(PollingSensor):

    def __init__(self, sim, config):
        PollingSensor.__init__(self, sim, config)
        self.logger = logging.getLogger("Accelerometer")
        
        self.data = namedtuple('AccelerometerData', ['t', 'x', 'y', 'z'])

        # Quantities for converting to raw values
        self.sensor_input_range = (- 4 * 9.81, 4 * 9.81)  # Gravity * g force (to convert 4 G to m/s^2)
        self.sensor_output_range = (-2048, 2048)  # @todo: get this from config

        # Conversion
        self._ms2_to_g = 1.0/9.81  # Conversion multiplier for m/s^2 to G force

        
    def create_step_samples(self, dt_usec):
        
        # Pod acceleration (x)
        pod_start_accel = self.sim.pod.last_acceleration
        pod_end_accel = self.sim.pod.acceleration
        
        # Create the samples (lerp between the times)
        sample_data = self._lerp(pod_start_accel, pod_end_accel)
        sample_times = sample_times = self._get_sample_times(dt_usec)

        # @todo: apply a rotation matrix to simulate the actual 
        z_accel = 9.81  # Gravity
        # @todo: remove the y accel -- it's just for testing whether or not we are getting data into the FCU
        return [self.data(t, sample_data[i], 0, z_accel) for i, t in enumerate(sample_times)]
        
    def to_raw(self, sample):
        """ Convert a sample to its raw form for the FCU """
        # @todo: This depends on mode (e.g. 4g, 8g, etc.) -- right now it's 4g
        # Note: The resolution is signed 2^12, so 1 bit for sign and 2^11 for data, giving a range of (-2048, 2048)
        # @todo: ^ Is the resolution changeable? Will we get that from the FCU at runtime? How to get that into the config? Inject per sensor from the FCU? 
        # @todo: what happens if the G force goes above the highest value? 
        # Note: 1G = 9.81m/s^2

        xyz = np.array((sample.x, sample.y, sample.z))
        # xyz = np.clip(xyz, *self.sensor_input_range)   # Clip to the input range (4g) to avoid  (Note: np.interp clips)
        xyz = np.interp(xyz, self.sensor_input_range, self.sensor_output_range)  
        return self.data(sample.t, *xyz.astype(int))
        
    def from_raw(self, sample):
        """ Convert the raw data format to SI units """
        xyz = np.array((sample.x, sample.y, sample.z))
        return self.data(sample.t, *np.interp(xyz, self.sensor_output_range, self.sensor_input_range))
        
        
class AccelerometerTestListener(object):
    def __init__(self, sim, config=None):
        self.sim = sim
        self.config = config
        
    def step_callback(self, sensor, samples):
        for sample in samples:
            pass
            #print "AccelerometerSensor sample: {}; raw: {}; from_raw: {}".format(sample, sensor.to_raw(sample), sensor.from_raw(sensor.to_raw(sample)))