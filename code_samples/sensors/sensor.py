#!/usr/bin/env python

from collections import deque

class Sensor:

    def __init__(self, world, config):
        self.world = world
        self.config = config
        
        self.thing_being_sensed = self.world.thing_being_sensed

        # Sampling
        self.sampling_rate_hz = 250
        self.queue = deque()
        
    def step(self, dt_usec):
        # Note: sensors are typically stepped after the physics step. 
        self.create_samples(dt_usec)
    
    def create_samples(self, dt_usec):
        last_value = self.thing_being_sensed.last_value
        this_value = self.thing_being_sensed.current_value
        
        # Calculate the number of samples we need for this timestep, accounting for overflow
        
        # Create reasonable values for the sensor for the time that's passed
        # Linspace between last value and this value
        for value in np.linspace(last_value, this_value, n_samples)  # or something; @todo: fix the arguments.
            self.queue.appendleft(self.create_sample(value))
        
    def create_sample(self, true_value):
        # Create a sample (true value + noise and perturbations)
        pass
        

class InterruptingSensor(Sensor):
    
    def __init__(self, world, config):
        super(InterruptingSensor, self).__init__(world, config)
        pass

    def set_isr(self, fn_ptr):
        pass  # Do we really want to use function pointers here? maybe just use the pod directly? 
        

class ContrastSensor(InterruptingSensor):
    
    def __init__(self, world, config):
        super(ContrastSensor,self).__init__(world, config)
        # Need to know about the pod (for position) and the tube (for the stripes)
        # Note: this sensor doesn't just spit out values, it calls an interrupt when the value changes. hmm...
        # Maybe register a callback and set a "pin"?
        
    def step(self, dt_usec):
        # Call the interrupt 
        pass
    
    def create_sample(self, true_value):
        pass
