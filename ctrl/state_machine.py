#!/usr/bin/env python

class CtrlStateMachine:
    
    def __init__(self):
        self.IDLE = 0
        self.READY = 1
        self.PUSH = 2
        self.COAST = 3
        self.BRAKE = 4
        self.EGRESS = 5
        
        self.state = self.IDLE
        
        
        self.mode = 'MANUAL'  # MANUAL|AUTO
        self.tests_passed = False
        self.pusher_interlock = False
        self.accel_confirmed = False
        
    def reset(self):
        self.mode = 'MANUAL'  # MANUAL|AUTO

        # IDLE state exit criteria
        self.tests_passed = False
        self.auto_mode = False

        # READY state exit criteria
        self.pusher_interlock = False
        self.accel_confirmed = False

        # PUSH state exit criteria
        self.pusher_separation = False
        self.push_timeout = False

        # COAST state exit criteria
        self.coast_timeout = False  # coast timeout gives us a bit of time to get clear of the pusher
        # @todo: do we want to have something that keeps track of when to turn over control to a braking controller? 
        # Or do we want to have the braking controller take over after the timeout and get us to a stop? Either way -- 

        # BRAKE state exit criteria
        self.brake_stopped = False

        # EGRESS state exit criteria
        # this is handled by command from the ground station. Egress automatically puts us in manual mode; we will send it back to IDLE when we've egressed.
        pass
        
        # @todo: what about executing things like start hover, stop hover, move things to a known state, operate cooling, etc.
        #  - cooling is not fully a separate subsystem I think, but it might be. Maybe just manual/auto modes? 
        
    def init(self):
        self.tests_passed = False
        self.state = self.IDLE
        
    def process(self):
        pass
            
    def run(self):
        pass