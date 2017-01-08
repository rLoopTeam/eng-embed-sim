#!/usr/bin/env python

from units import Units
import math

class HoverEngineForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

        self.lift_a = self.config.lift.a
        self.lift_b = self.config.lift.b
        self.lift_c = self.config.lift.c
        self.lift_k = self.config.lift.k
        
    def get_force(self):
        """ 
        Get lift provided by hover engines 
        @see rPod Engine Model v2 from @ashtorak
        
        "a", "b", "c" are fit parameters
        "k" relates RPM to velocity

        F(height, velocity, RPM) = a*e^(b*h) * tan^-1( c(v + kr) ) 
        
        """
        
        """
        height = self.sim.pod.height
        velocity = self.sim.pod.velocity
        rpm = self.sim.pod.hover_engines.rpm  # @todo: implement this. Do we want to split the hover engines? 
    
        lift_force = self.a * math.exp(self.b * height) * math.atan(self.c * (velocity + self.k * rpm))
        return lift_force * 8
        """
        height = self.sim.pod.height  # This won't work -- we need hover engine height in meters
        height = .008  # just for testing -- need to get this somewhere
        velocity = self.sim.pod.velocity
        #rpm = self.sim.pod.hover_engines.rpm  # @todo: implement this. Do we want to split the hover engines? 
        rpm = 0
        
        # Lift
        p1 = math.exp(self.lift_b * height)
        p2 = math.atan(self.lift_c * (velocity + self.lift_k * rpm))
        z = self.lift_a * p1 * p2
        print "Hover engine lift: {} (RPM: {}, pod velocity: {})".format(z, rpm, velocity)
        return (0, 0, z)
        
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
    