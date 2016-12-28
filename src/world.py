#!/usr/bin/env python

import logging

from pod import Pod
from tube import Tube
from pusher import Pusher

logging.basicConfig()
logger = logging.getLogger('world')
logger.setLevel(logging.DEBUG)

class World:
    
    def __init__(self, config):
        self.logger = logging.getLogger("World")

        self.config = config
        self.pod = Pod(self, self.config.pod)
        self.tube = Tube(self, self.config.tube)
        self.pusher = Pusher(self, self.config.pusher)
        
        # Do some configuration here? 
        self.logger.info("World initialized")
        
    def reset(self):
        """ Reset the world """    
        pass
    
    def step(self, dt_usec):
        # Update the pod, pusher, and tube.
        # Note that the pod and pusher relationship is handled here (?)

        self.pusher.step(dt_usec)
        self.pod.step(dt_usec)
        
        
if __name__ == "__main__":
    world = World()