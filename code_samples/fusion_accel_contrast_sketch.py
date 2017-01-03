#!/usr/bin/env python

from collections import deque

class strAccel:
    def __init__(self):
        self.fifo = deque()

        # Current values
        self.t = 0.0
        self.p = 0.0
        self.a = 0.0
        self.v = 0.0

        self.t0 = 0.0   # This will be reset when there is a higher-confidence position value
        self.p0 = 0.0
        self.a0 = 0.0
        self.v0 = 0.0
        
        # Will be calculated per step based on time elapsed
        self.p_confidence = 0.0  
        self.v_confidence = 0.0
        
        self.time_since_last_sample = 0.0

        # Accelerometer has a position offset -- when we get a position (and time) value from the contrast sensors, update the accelerometer's offset
        # In the processing, handle the accelerometer pos estimation first. Then handle the contrast sensors
        #   If the contrast sensor position differs from the accel position estimation, alter the accel offset to correct.
        #   The assumption is that the accel sensor, at 800hz, should update "continuously" -- we'll process the contrast sensor data soon enough after
        #   that that we have a comparable time. If not, we'll need to use speed in the mix to estimate position offset. 
        # Get the accel position. When we know what our position is, change the accel position offset 


def process_x_accel(strAccel, new_accel_value):
    """ Process an x acceleration value (calculated elsewhere from x,y,z) """
    
        
        t_sec = dt_usec / 1000000
        
        # v*t + 1/2*a*t^2
        self.position += self.velocity * t_sec + 0.5 * self.acceleration * (t_sec ** 2)
        
        # vf = v0 + at
        self.velocity = self.velocity + self.acceleration * t_sec

        # @todo: change this to log to a data stream or file? 
        self.logger.info(self.get_csv_row())

        # Update time
        self.elapsed_time_usec += dt_usec