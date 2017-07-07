#!/usr/bin/env python

import logging
import numpy as np
from collections import namedtuple

from units import Units
from config import Config
from sensors import PollingSensor

"""
Notes (conversation with @safetylok and @piense 1/27/17)
forward looking laser
- 9600 baud
- ASCII mode? -- david said to put it in binary (too costly to do the conversion)
- 50hz -- (lachlan's equations are tuned for that rate)
- internal averaging -- internal 200 with averaging, output at 50hz
- we don't know what the data will look like
    - distance in mm -- Dxxxxx (xs represent mms), ascii (need to change over to binary)
    - Need to feed that into the sc16is
"""


class LaserDistSensor(PollingSensor):
    """ Laser Opto Sensor (height sensors) """
    """
    @see http://www.micro-epsilon.com/download/manuals/man--optoNCDT-1320--en.pdf, page 55 (p57 for behavior)
    """
    
    def __init__(self, sim, config):
        PollingSensor.__init__(self, sim, config)
        self.logger = logging.getLogger("LaserOptoSensor")
        
        self.logger.info("Initializing Laser Distance Sensor")
        
        # Data types
        # @todo: does this also return velocity/accel? 
        self.data = namedtuple('LaserDistSensorData', ('t_usec', 'distance'))
        
    def create_step_samples(self, dt_usec):
        # Create distance samples
        
        start_dist = self.sim.track.length - self.sim.pod.last_position
        end_dist = self.sim.track.length - self.sim.pod.position
        
        samples = self._lerp(start_dist, end_dist)
                
        # Add noise. @todo: we might want to do this after we adjust for gaps? 
        samples += self._get_gaussian_noise(samples, self.noise_center, self.noise_scale)
        
        sample_times = self._get_sample_times(dt_usec)

        return [self.data(t, samples[i]) for i, t in enumerate(sample_times)]

    def to_raw(self, sample):
        """ Convert a single sample to its raw form """
        # Note: 'Real' form is m, raw form is mm
        return self.data(sample.t_usec, int(sample.distance * 1000))

    def from_raw(self, sample):
        """ Map a raw sample (self.data format) to its real value """
        return self.data(sample.t_usec, sample.distance / 1000.0)

    def get_csv_headers(self):
        return self.data._fields


class LaserDistTestListener(object):
    def __init__(self, sim, config=None):
        self.sim = sim
        self.config = config
        self.logger = logging.getLogger("LaserDistTestListener")
        
    def step_callback(self, sensor, samples):
        for sample in samples:
            self.logger.debug("Samples: {}".format(samples))
