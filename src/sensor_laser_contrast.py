#!/usr/bin/env python

import numpy as np
import logging 

from sensors import InterruptingSensor    
    
class LaserContrastSensor(InterruptingSensor):

    def __init__(self, sim, config):
        InterruptingSensor.__init__(self, sim, config)
        self.logger = logging.getLogger("LaserContrastSensor")
        
    def create_step_samples(self, dt_usec):
        
        # Stripe positions
        strip_starts = self.sim.tube.reflective_strips
        strip_ends = self.sim.tube.reflective_strip_ends

        # Pod positioning so that we can check for gap traversal
        pod_start_pos = self.sim.pod.last_position
        pod_end_pos = self.sim.pod.position
        
        # Get the start and end indices that are in our step range
        strip_start_indices_in_step_range = np.nonzero(np.logical_and(strip_starts >= pod_start_pos, strip_starts < pod_end_pos))[0]  # [0] because np.nonzero deals with n dimensions, but we only have one
        #strip_end_indices_in_step_range = np.nonzero(np.logical_and(strip_ends >= pod_start_pos, strip_ends < pod_end_pos))[0]  # [0] because np.nonzero deals with n dimensions, but we only have one

        # Get the start and end positions that are in our step range
        strip_start_positions_in_step_range = np.array(strip_starts)[strip_start_indices_in_step_range]
        #strip_end_positions_in_step_range = np.array(strip_ends)[strip_end_indices_in_step_range]
        
        start_time = self.sim.elapsed_time_usec
        end_time = start_time + dt_usec
        
        strip_start_times = self._lerp_map_int(strip_start_positions_in_step_range, pod_start_pos, pod_end_pos, start_time, end_time)
        strip_start_times = np.interp(strip_start_positions_in_step_range, [pod_start_pos, pod_end_pos], [start_time, end_time])
        #strip_end_times = self._lerp_map_int(strip_end_positions_in_step_range, pod_start_pos, pod_end_pos, start_time, end_time)
        
        #strip_start_samples = np.hstack((strip_start_times.reshape((-1,1)), np.ones((len(strip_start_times), 1), dtype=np.int)))
        #strip_end_samples = np.hstack((strip_end_times.reshape((-1,1)), np.zeros((len(strip_end_times), 1), dtype=np.int)))
        
        strip_start_flags = np.ones(len(strip_start_times), dtype=np.int)
        start_rec = np.rec.fromarrays( (strip_start_times, strip_start_flags), names=('time_usec', 'pin_value'))

        #strip_end_flags = np.zeros(len(strip_end_times), dtype=np.int)
        #end_rec = np.rec.fromarrays( (strip_end_times, strip_end_flags), names=('time_usec', 'pin_value'))

        #samples = np.hstack((start_rec, end_rec))
        samples = start_rec
        samples.sort()
        return samples
        
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
        

class LaserContrastTestListener(object):
    def __init__(self, config=None):
        self.config = config
        self.n_gaps = 0
        
    def step_callback(self, sensor, samples):
        return
        for sample in samples:
            # Note: sample[0] is the sample time, sample[1] is the height value
            print "LaserContrastSensor sample: {}".format(sample)
            
            