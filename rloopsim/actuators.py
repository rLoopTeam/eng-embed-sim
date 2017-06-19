#!/usr/bin/env python

        
class StepperMotor:
    
    def __init__(self, properties, connections):
        self.properties = properties
        self.connections = connections  # Power, control, sensor output, heat sink, etc.
        self.power = self.connections.power
        
        self.power.add_mode("move", 0.5)  # 0.5 amps when moving. Get this from properties?
        self.power.add_mode("hold", 0.3)  # 0.3 amps when holding. "
        
        self.turn_position = 0.   # turn counter -- e.g. 3.2 turns to the right + 1 turn to the left = 2.2 turns
        
    def move(self, direction, speed_mps, dt_usec):
        """ Move the motor """
        # @todo: define the signature for this 
        if self.power.draw("move", dt_usec):
            # Move the motor
        else:
            return False  # Should this be a fault code? 
    
    def hold(self, dt_usec):
        """ Hold the motor """
        
        # @todo: define how we draw power -- probably a mode? 
        if self.power.draw("hold", dt_usec):
            # Don't do anything
            pass
        else:
            # Raise a fault?
            pass

    