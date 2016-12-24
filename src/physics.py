#!/usr/bin/env python


class PhysicsBody1D:
    """ A simple 1 dimensional physics object """
    
    # Note: All units are SI

    def __init__(self):
                
        # Note: mass can change during simulation, but usually doesn't
        self.mass = 0.0            # kg
        
        # Volatile
        self.acceleration = 0.0    # m/s^2
        self.velocity = 0.0        # m/s
        self.position = 0.0        # m
        
        self.net_force = 0.0       # Newtons
        
    def apply_force(self, force_N):
        """ Apply a force (Newtons) to the object """
        self.net_force += force_N
        
    def step(self, dt_usec):
        """ Take a single step (called during simulation) """
        # @todo: pdate acceleration, velocity, and position based on net force applied over dt_usec
        pass
        
        
if __name__ == "__main__":
    body = PhysicsBody1D()
    body.mass = 