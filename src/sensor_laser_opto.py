#!/usr/bin/env python

import logging
import numpy as np
from collections import namedtuple

from units import Units
from config import Config
from sensors import PollingSensor

class LaserOptoSensors(list):
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
        
        for i, sensor_config in enumerate(self.config):
            sensor_config['id'] = i   # Inject the sensor ID
            sensor_config['name'] = "laser_opto_{}".format(i)   # Inject the sensor name
            self.append(LaserOptoSensor(self.sim, Config(sensor_config)))

    def add_step_listener(self, listener):
        pass

class LaserOptoSensor(PollingSensor):
    
    def __init__(self, sim, config):
        PollingSensor.__init__(self, sim, config)
        self.logger = logging.getLogger("LaserOptoSensor")
        
        # Get the height offset for this sensor?
        self.he_height_offset = Units.SI(self.config.he_height_offset)
                
        # Data types
        self.data = namedtuple('LaserOptoSensorData', 'time height')
        
    def create_step_samples(self, dt_usec):
        # Create height samples
        
        # @todo: check error if step straddles a gap

        height_samples = self._lerp(self.sim.pod.last_he_height, self.sim.pod.he_height)
        height_samples += self.he_height_offset
        
        # Add noise. @todo: we might want to do this after we adjust for gaps? 
        height_samples += self._get_gaussian_noise(height_samples, self.noise_center, self.noise_scale)
        
        # Gap positions
        # Pod positioning so that we can check for gap traversal
        pod_start_pos = self.sim.pod.last_position
        pod_end_pos = self.sim.pod.position

        gaps = np.array(self.sim.track.track_gaps)
        
        # Calculate the gap indices that we want to check. Make sure to include gaps that start before the beginning position but straddle the start
        # Note: We might check an extra gap index here or there, but it will be handled properly by the calculations below
        gap_check_start_pos = pod_start_pos - self.sim.track.track_gap_width # Check for gap starts a little before the pod start position
        gap_indices_in_step_range = np.nonzero(np.logical_and(gaps >= gap_check_start_pos, gaps <= pod_end_pos))[0]  # [0] because np.nonzero deals with n dimensions, but we only have one

        #self.logger.debug("Gap indices in step range {} to {}: {}".format(pod_start_pos, pod_end_pos, gap_indices_in_step_range))
        gap_positions_in_step_range = np.array(gaps)[gap_indices_in_step_range]
        
        #self.logger.debug("Gap positions in step range: {}".format(gap_positions_in_step_range))
                
        # If we're traversing any gaps this step...
        if len(gap_positions_in_step_range):

            # Get the x position of each sample in this step to see if it is over a gap
            sample_positions = self._lerp(pod_start_pos, pod_end_pos)
            
            # Find the samples that are over a gap (if any)
            over_gap_indices = []  # Note: can't use a np array here since no extending
            for gap_start_pos in gap_positions_in_step_range:
                gap_end_pos = gap_start_pos + self.sim.track.track_gap_width
                over_gap_indices.extend(np.nonzero(np.logical_and(sample_positions >= gap_start_pos, sample_positions <= gap_end_pos))[0].tolist())

            #self.logger.debug("Over gap indices: {}".format(over_gap_indices))

            # Adjust the samples that are over gaps
            if len(over_gap_indices) > 0:
                self._adjust_samples_for_gaps(height_samples, over_gap_indices)

        sample_times = self._get_sample_times(dt_usec)

        # Return our (possibly adjusted) height samples
        #self.logger.debug("Created {} samples".format(len(height_samples)))

        # Turn the two 1d vectors of values [time, time, ...] and [height, height, ...] into a two column array like [[time, height], [time, height], ...]
        # @see http://stackoverflow.com/questions/5954603/transposing-a-numpy-array
        # Note: for other sensors, if you have multiple values for your samples (e.g. samples are like [[v0, v1], [v0, v1], ...]), you don't need to reshape the samples
        #return np.hstack((sample_times.reshape((-1,1)), height_samples.reshape((-1,1))))  # Works, but changing over to using namedtuples
        
        return [self.data(t, height_samples[i]) for i, t in enumerate(sample_times)]

    def _adjust_samples_for_gaps(self, samples, indices):
        """ Adjust the samples at the given indices as if they were over a gap """
        # Example: find the contiguous groups of samples so that we can apply a function to multiple 
        # contiguous_sample_groups = np.split(indices, np.where(np.diff(indices) != 1)[0]+1)
        # print contiguous_sample_groups
        samples[indices] += 12.27 # @todo: adjust appropriately to match data collected at test weekend -- this just adds 0.5"


class LaserOptoTestListener(object):
    def __init__(self, config=None):
        self.config = config
        self.n_gaps = 0
        
    def step_callback(self, sensor, samples):
        for sample in samples:
            # Note: sample[0] is the sample time, sample[1] is the height value
            if sample.height > .028:  # we're adding 12.7 mm or so for right now to test this
                self.n_gaps += 1
                #print "GAP FOUND! {},{} -- {} found so far".format(t, sensor.sim.pod.position, self.n_gaps)
