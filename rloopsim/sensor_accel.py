#!/usr/bin/env python

import numpy as np
import logging 
from collections import namedtuple
from operator import attrgetter  # For sorting named tuples
from units import Units

from sensors import PollingSensor    
    
class Accelerometer(PollingSensor):

    def __init__(self, sim, config):
        PollingSensor.__init__(self, sim, config)
        self.logger = logging.getLogger("Accelerometer")

        self.logger.info("Initializing Accelerometer {}".format(self.config.id))
                
        self.data = namedtuple('AccelerometerData', ['t_usec', 'raw_x', 'raw_y', 'raw_z', 'real_x', 'real_y', 'real_z'])

        # Quantities for converting to raw values
        raw_min = self.config.raw_min
        raw_max = self.config.raw_max
        real_min = Units.SI(self.config.real_min)
        real_max = Units.SI(self.config.real_max)

        self.sensor_input_range = (real_min, real_max)
        self.sensor_output_range = (raw_min, raw_max)
        
    def create_step_samples(self, dt_usec):
        
        # Pod acceleration (x)
        pod_start_accel = self.sim.pod.last_acceleration
        pod_end_accel = self.sim.pod.acceleration
        
        # Create the samples (lerp between the times)
        sample_data = self._lerp(pod_start_accel, pod_end_accel)
        sample_times = sample_times = self._get_sample_times(dt_usec)

        # @todo: apply a rotation matrix to simulate the actual 

        # NOTE: Accel is mounted such that it is rotated 90 degrees in the horizontal plane such that:
        #       +y accel = +x pod reference frame, +x accel = -y pod reference frame
        #       ^ This is the format for the data.
        # @todo: move this to config somehow (tbd)

        # Map real values to sample values

        samples = []
        for i, t in enumerate(sample_times):
            real_x = 0
            real_y = sample_data[i]
            real_z = 9.81  # Accel due to gravity

            # @todo: Apply a rotation matrix? 

            # Map 
            xyz = np.array((real_x, real_y, real_z))
            # Add some noise (in G's)
            xyz += np.random.normal(self.noise_center, Units.SI(self.noise_scale), 3)
            xyz = np.interp(xyz, self.sensor_input_range, self.sensor_output_range)  
            xyz = xyz.astype(int)
            samples.append(self.data(t, xyz[0], xyz[1], xyz[2], real_x, real_y, real_z))

            #samples += self._get_gaussian_noise(samples, self.noise_center, self.noise_scale)            

        return samples
                        
    def to_raw(self, sample):
        """ Convert a sample to its raw form for the FCU """
        # @todo: This depends on mode (e.g. 4g, 8g, etc.) -- right now it's 4g
        # Note: The resolution is signed 2^12, so 1 bit for sign and 2^11 for data, giving a range of (-2048, 2048)
        # @todo: ^ Is the resolution changeable? Will we get that from the FCU at runtime? How to get that into the config? Inject per sensor from the FCU? 
        # @todo: what happens if the G force goes above the highest value? 
        # Note: 1G = 9.81m/s^2

        xyz = np.array((sample.real_x, sample.real_y, sample.real_z))
        # xyz = np.clip(xyz, *self.sensor_input_range)   # Clip to the input range (4g) to avoid  (Note: np.interp clips)
        xyz = np.interp(xyz, self.sensor_input_range, self.sensor_output_range)  
        return self.data(sample.t_usec, *xyz.astype(int))
        
    def from_raw(self, sample):
        """ Convert the raw data format to SI units """
        xyz = np.array((sample.x, sample.y, sample.z))
        return self.data(sample.t_usec, *np.interp(xyz, self.sensor_output_range, self.sensor_input_range))
        
    def get_csv_headers(self):
        return self.data._fields
    
class AccelerometerTestListener(object):
    def __init__(self, sim, config=None):
        self.sim = sim
        self.config = config
        
    def step_callback(self, sensor, samples):
        for sample in samples:
            pass
            #print "AccelerometerSensor sample: {}; raw: {}; from_raw: {}".format(sample, sensor.to_raw(sample), sensor.from_raw(sensor.to_raw(sample)))
            #print(samples)