#!/usr/bin/env python

#!/usr/bin/env python
# coding=UTF-8

# File:     sensors.py
# Purpose:  Sensor classes
# Author:   Ryan Adams (@ninetimeout)
# Date:     2016-Dec-17

# NOTE: Please add your name to 'Author:' if you work on this file. Thanks!

# Note: all units are SI: meters/s^2, meters/s, and meters. Time is in microseconds (?)

from units import Units
from collections import deque
import numpy as np

class PollingSensor:
    """ Sensor that provides a data stream  """
    
    """
    Note: Sensors will need inputs from the outside world -- sensors will need to 'sample' the world. 
          - How do we connect a sensor to what it needs to measure? In the constructor? 
          - Probably want an id as well for logging purposes.
    
    
    """

    def __init__(self, sim, config):
        
        self.sim = sim
        self.config = config

        # Configuration

        # Grab the fixed timestep from the sim. If we wanted to use a variable timestep we would need to do the next calculations in the lerp function
        self.fixed_timestep = Units.SI(self.sim.config.fixed_timestep)
        self.sampling_rate = Units.SI(self.config.sampling_rate)  # Hz

        self.noise_scale = self.config.noise_scale  # Standard deviation # @todo: give this a default value (0?) so it's not required in the config

        # Calculated
        self.samples_per_step = self.sampling_rate * self.fixed_timestep
        self.sample_pct_of_step = 1.0/self.samples_per_step  # For lerping

        # Volatile
        self.next_start = 0.0
              
    def create_step_samples(self, start_value, end_value, noise_scale=0.0):
        if self.next_start >= 1:
            self.next_start -= 1
            return []
        else:
            # Get our positions for lerping between the values. Don't care about actual time here since we've already calculated that into sample_pct_of_step
            lerp_positions = np.arange(self.next_start, 1, self.sample_pct_of_step)
            # Calculate how far into the next step we should take our first sample during that step
            # E.g. if we took 2 samples this step at 0.0 and 0.8, we might start our next sample at 0.6 (assuming we wanted to take a sample every 0.8 * fixed_timestep seconds)
            self.next_start = self.sample_pct_of_step - (1 - lerp_positions[-1])

            # Handle lerping 
            samples = start_value + lerp_positions * (end_value - start_value)
            if noise_scale > 0:
                # Add noise if we have any
                return samples + np.random.normal(0.0, noise_scale, len(samples))
            else:
                # No noise
                return samples
            

class LaserOptoSensor(PollingSensor):
    
    def __init__(self, sim, config):
        PollingSensor.__init__(self, sim, config)  # @todo: is this right? 
        
        # Get the height offset for this sensor
        pass

    def get_step_samples_with_gap(self):
        # Get the height of the pod
        samples = self.create_step_samples(self.sim.pod.last_height, self.sim.pod.height, self.noise_scale)

        # Need the position of each sample to see if it is over a crack
        sample_positions = self.create_step_samples(self.sim.pod.last_position, self.sim.pod.position)
        
        # @todo: fix this to use some numpy goodness instead of nested for loops
        for gap in self.sim.tube.track_gaps:
            for i, pos in enumerate(sample_positions): 
                if pos >= gap and pos <= (gap + self.sim.tube.track_gap_width):
                    # We're over a gap in the track
                    samples[i] = self.get_gap_value(samples[i])
        
        # @todo: what about adding noise? Should we do that before or after we jump the values? 
        return samples

    def get_gap_value(self, actual_value):
        # How to calculate this? Should we add 0.5" as if it correctly detected it? Need to look at the data
        return 50.48  # @todo: Actually we'll want to derive this from the test weekend data, but for right now let's do this

        
# ---------------------------
# Just notes/sketches below here        
        
        
class DataCollector:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
    
    def step(self, dt_usec):
        pass  # Defer this to subclasses?
        """
        Might look like: 
        - value0 = self.last_height
        - value1 = self.height
        - samples = self.sensor.create_step_samples(value0, value1)
        - self.writers.write(samples.asbin())
        """
        


# Inherit from someone? 
class InterruptingSensor():
    """ A sensor that can call a function if it detects an event during a step """
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
        
    def step(self, dt_usec):
        """ Detect event(s) and call the callback if detected """
        """
        if some_event_happened: 
            self.callback(pin_state)  # Does it get pin state here? 
        """

    def set_pin_change_callback(self, fn):
        self.callback = fn
        
    


class SensorBuffer:
    """ Collects sensor values and manages their storage/filtering/redirecting? """

    def __init__(self, sim, config):
        pass



import random

class LaserDistanceSensor():
    
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
        self.precision = 14  # 14 bits
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
    
class AccelData:
    def __init__(self):
        """
        # @see eng-software-pod/FIRMWARE/PROJECT_CODE/LCCM655__RLOOP__FCU_CORE/ACCELEROMETERS/fcu__accel__ethernet.c
        //fault flags
        vNUMERICAL_CONVERT__Array_U32(pu8Buffer, u32MMA8451__Get_FaultFlags(u8Device));
        pu8Buffer += 4U;

        //X Raw
        vNUMERICAL_CONVERT__Array_S16(pu8Buffer, s16MMA8451_FILTERING__Get_Average(u8Device, AXIS_X));
        pu8Buffer += 2U;

        //Y Raw
        vNUMERICAL_CONVERT__Array_S16(pu8Buffer, s16MMA8451_FILTERING__Get_Average(u8Device, AXIS_Y));
        pu8Buffer += 2U;

        //Z Raw
        vNUMERICAL_CONVERT__Array_S16(pu8Buffer, s16MMA8451_FILTERING__Get_Average(u8Device, AXIS_Z));
        pu8Buffer += 2U;

        //X Accel
        vNUMERICAL_CONVERT__Array_F32(pu8Buffer, f32MMA8451_MATH__Get_GForce(u8Device, AXIS_X));
        pu8Buffer += 4U;

        //Y Accel
        vNUMERICAL_CONVERT__Array_F32(pu8Buffer, f32MMA8451_MATH__Get_GForce(u8Device, AXIS_Y));
        pu8Buffer += 4U;

        //Z Accel
        vNUMERICAL_CONVERT__Array_F32(pu8Buffer, f32MMA8451_MATH__Get_GForce(u8Device, AXIS_Z));
        pu8Buffer += 4U;

        //Pitch
        vNUMERICAL_CONVERT__Array_F32(pu8Buffer, f32MMA8451_MATH__Get_PitchAngle(u8Device));
        pu8Buffer += 4U;

        //Roll
        vNUMERICAL_CONVERT__Array_F32(pu8Buffer, f32MMA8451_MATH__Get_RollAngle(u8Device));
        pu8Buffer += 4U;
        
        """


        self.dtype = np.dtype([
                ('fault_flags', np.uint32),
                ('raw_x', np.int16),
                ('raw_y', np.int16),
                ('raw_z', np.int16),
                ('accel_x', np.float32),
                ('accel_y', np.float32),
                ('accel_z', np.float32),                
                ('pitch', np.float32),
                ('roll', np.float32),                
        ])
        
        self._accel_indices = [0, 4, 5, 6]
        
        self.data = np.array([(0, 0.1, 12, 1234, 0.12345678901234, 0.12345678901234, 0.12345678901234, 0.12345678901234, 0.12345678901234)], dtype=self.dtype)
        self.data['fault_flags'] = 0
        self.data['raw_x'] = 0.1
        self.data['raw_y'] = 12
        self.data['raw_z'] = 31929
        self.data['accel_x'] = 0.12345678901234
        self.data['accel_y'] = 0.23456789012345
        self.data['accel_z'] = 0.34567890123456
        self.data['pitch'] = 0.1000
        self.data['roll'] = 0.2000


        print len(self.data.tostring(order="C"))
                
    def pack_safeudp_full(self):
        return self.data.tostring(order="C")
        
    def pack_safeudp_cal(self):
        print self.data[0]
        
        return self.data[0].tostring()

class AccelData2:
    
    def __init__(self):
        self.dtype = np.dtype('uint32, int16, int16, int16, float32, float32, float32, float32, float32')
        self.data = np.array([(0, 1, 12, 1234, 0.12345678901234, 0.12345678901234, 0.12345678901234, 0.12345678901234, 0.12345678901234)], dtype=self.dtype)
        print np.asmatrix(self.data)


if __name__ == "__main__":

    ad2 = AccelData2()
    exit()
    
    ad = AccelData()
    print len(ad.pack_safeudp_full())
    print len(ad.pack_safeudp_cal())
    print ""
    
    dt_usec = 100002
    sensor = LaserDistanceSensor()
    sensor.sampling_rate_hz = 200
    for i in xrange(10):
        sensor.step(dt_usec)
        print len(sensor.fifo)
    