#!/usr/bin/env python

from units import Units
import math
import numpy as np

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
        height = self.sim.pod.he_height
        #height = .008  # just for testing -- need to get this somewhere
        velocity = self.sim.pod.velocity
        #rpm = self.sim.pod.hover_engines.rpm  # @todo: implement this. Do we want to split the hover engines? 
        rpm = 0
        
        # Lift
        p1 = math.exp(self.lift_b * height)
        p2 = math.atan(self.lift_c * (velocity + self.lift_k * rpm))
        z = self.lift_a * p1 * p2
        #print "Hover engine lift: {} (RPM: {}, pod velocity: {})".format(z, rpm, velocity)
    
    
        # Drag (thanks @capsulecorplab!)
        # Note: this doesn't take into account the RPM
        """
        NOTE: the following doesn't work (problem with the >30 calculation it seems...)
        v = velocity
    	h = height
    	#RPM = self.sim.pod.hover_engines.RPM
    	if v < 15:
     		x = - ( (0.035557*h - 0.057601) * v**3 + (- 0.8*h + 12.56) * v**2 + (2.1777*h - 27.9994) * v)
    	elif v > 30:
    		x = - ( (-0.000565367*h + 0.009223) * v**2 + (0.17878*h - 3.02658)*v + (-29.71 * h + 500.93))
    	else:
    		x = - ( (-0.008889*h + 0.0120001) * v**2 + (-0.244438*h + 2.59993)*v + (-25.667 * h + 450))

        #print "Drag force for 1 hover engine is {}".format(x)
        """
        
        # Alternative method for HE drag (manual curve fitting and linear system solving for o1 and o2 (f(0.006) = 150, f(0.012) = 65))
        o1 = 235
        o2 = -14166.667
        coeff = height * o2 + o1
        x = - coeff * (-np.exp(-.16*velocity)+1) * (1.6*np.exp(-0.2*velocity) + 1)

        #print "Calculated he drag (1 engine) at height {} and velocity {}: {}".format(height, velocity, x)

        # @todo: is the drag for a single hover engine or all 8? 
        return (8*x, 0, z * 8)  # *8 because 8 hover engines

        """
        Another possible way:
        coeff 150 = 6mm hover height, coeff 65 = 12mm hover height
        drag = coeff * (-exp(-.16x)+1) * (1.6*exp(-0.2x) + 1)  # Found by manual fitting to curves in rPod Engine Model v2.xlsx
        
        """
        
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
    