#!/usr/bin/env python

from units import Units
import math

class HoverEngineForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

        """
        self.a = self.config.a
        self.b = self.config.b
        self.c = self.config.c
        self.k = self.config.k
        """
        
    def get_force(self):
        """ 
        Get lift provided by hover engines 
        @see rPod Engine Model v2 from @ashtorak
        
        F(height, velocity, RPM) = a*e^(b*h) * tan^-1( c(v + kr) ) 
        
        """
        
        
        """
        height = self.sim.pod.height
        velocity = self.sim.pod.velocity
        rpm = self.sim.pod.hover_engines.rpm  # @todo: implement this. Do we want to split the hover engines? 
    
        lift_force = self.a * math.exp(self.b * height) * math.atan(self.c * (velocity + self.k * rpm))
        return lift_force * 8
        """
        
        return (0, 0, 0)
        
    # If hover engines are turning, the drag is reduced but not zero
    # HE lift and drag for different velocities? One that Keith saw (about 3 months ago)
    # Stationary engine at 2000RPM is 2 N of drag (4N if it's not spinning)
    # At 120 m/s it has how much lift and how much drag? 
    # 22m/s spinning 13 lbs, not spinning 27lbs drag  (not spinning is 120N per engine, or 8x that for all engines)
    # 90 m/s stationary 4lbs, spinning 2 lbs drag
    # To look for it more, look around August 1 2016 in the numsim channel
    
    # Note: lift is 80% at 10, 90% at 30, and slowly gets more
    
    # Arx pax -- lift at a certain mass -- will climb about 2-3 mm as we get going faster
    
    # magnets are spinning at 20m/s when the motors are moving at 2000RPM
    