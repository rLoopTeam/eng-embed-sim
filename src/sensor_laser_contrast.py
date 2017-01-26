#!/usr/bin/env python

import numpy as np
import logging 
from collections import namedtuple
from operator import attrgetter  # For sorting named tuples

from sensors import InterruptingSensor    
    
class LaserContrastSensor(InterruptingSensor):

    def __init__(self, sim, config):
        InterruptingSensor.__init__(self, sim, config)
        self.logger = logging.getLogger("LaserContrastSensor")
        
        self.data = namedtuple('LaserContrastSensorData', ['t', 'pos', 'pin_state'])
        
    def create_step_samples(self, dt_usec):
        
        # Stripe positions
        strip_starts = self.sim.track.reflective_strips
        strip_ends = self.sim.track.reflective_strip_ends

        # Pod positioning so that we can check for gap traversal
        pod_start_pos = self.sim.pod.last_position
        pod_end_pos = self.sim.pod.position
        
        # Get the start and end indices that are in our step range
        strip_start_indices_in_step_range = np.nonzero(np.logical_and(strip_starts >= pod_start_pos, strip_starts < pod_end_pos))[0]  # [0] because np.nonzero deals with n dimensions, but we only have one
        strip_end_indices_in_step_range = np.nonzero(np.logical_and(strip_ends >= pod_start_pos, strip_ends < pod_end_pos))[0]  # [0] because np.nonzero deals with n dimensions, but we only have one

        # Get the start and end positions that are in our step range
        strip_start_positions_in_step_range = np.array(strip_starts)[strip_start_indices_in_step_range]
        strip_end_positions_in_step_range = np.array(strip_ends)[strip_end_indices_in_step_range]
        
        start_time = self.sim.elapsed_time_usec
        end_time = start_time + dt_usec
        
        strip_start_times = np.interp(strip_start_positions_in_step_range, [pod_start_pos, pod_end_pos], [start_time, end_time])
        strip_end_times = np.interp(strip_end_positions_in_step_range, [pod_start_pos, pod_end_pos], [start_time, end_time])
        
        # @todo: If we're not going to add in the x offset on the real sensors, we need to subtract that out here.
        start_data = [self.data(t, strip_start_positions_in_step_range[i], 1) for i, t in enumerate(strip_start_times)]
        end_data = [self.data(t, strip_end_positions_in_step_range[i], 0) for i, t in enumerate(strip_end_times)]
        
        ret = sorted(start_data + end_data, key=attrgetter('t'))
        #print "LaserContrastSensor data test: {}".format(ret)

        return ret
        #strip_start_samples = np.hstack((strip_start_times.reshape((-1,1)), np.ones((len(strip_start_times), 1), dtype=np.int)))
        #strip_end_samples = np.hstack((strip_end_times.reshape((-1,1)), np.zeros((len(strip_end_times), 1), dtype=np.int)))
        
        #strip_end_flags = np.zeros(len(strip_end_times), dtype=np.int)
        #end_rec = np.rec.fromarrays( (strip_end_times, strip_end_flags), names=('time_usec', 'pin_value'))

        #samples = np.hstack((start_rec, end_rec))

        #return samples
        
        # @todo: Probably need to calculate the position based on pod offset for these samples (instead of just time when the sample was taken)
        # ^ that would be another element in the sensor fields -- e.g. time, *pod* position, 1/0 for rising/falling
        
    def _lerp_map(self, x_vals, a0, a1, b0, b1):
        """ 
        Map the x_values in range [a0, a1] to their equivalent positions in range [b0, b1] 
        Example: 
            [a0, a1] = [12, 24], x_vals = [13, 22, 17], [b0, b1] = [100, 200]:
                => returns [ 108.33333333,  183.33333333,  141.66666667]
        """
        return b0 + (b1 - b0) * ((np.array(x_vals) - a0) / (a1 - a0))

    def _lerp_map_int(self, x_vals, a0, a1, b0, b1):
        """ Lerp map, but return ints. Code duplicated because function calls are expensive """
        return np.array(b0 + (b1 - b0) * ((np.array(x_vals) - a0) / (a1 - a0)), dtype=np.int)

    # @todo: move this to a listener; preferably one that can call the interrupts in "real" time
    def on_rising_edge(self):
        pass
        
    def on_falling_edge(self):
        pass
        
    def get_csv_headers(self):
        return self.data._fields


class LaserContrastTestListener(object):
    def __init__(self, sim, config=None):
        self.sim = sim
        self.config = config
        self.n_gaps = 0
        
    def step_callback(self, sensor, samples):
        return
        for sample in samples:
            # Note: sample[0] is the sample time, sample[1] is the height value
            print "LaserContrastSensor sample: {}".format(sample)
            
            