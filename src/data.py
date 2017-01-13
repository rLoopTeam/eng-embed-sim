!#/usr/bin/env python

class StepSummary:
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
        
    def step_callback(self, sensor, samples=None):
        """ Called by lots of different sensors and the pod itself """