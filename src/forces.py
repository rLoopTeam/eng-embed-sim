#!/usr/bin/env python

import numpy as np
from collections import namedtuple
from units import Units

class ForceExerter:
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
    
        self.step_listeners = []  # So we can act as a sensor

        self.name = None   # Deferred to subclasses; used for aggregatinglistener (for output)
        self.data = namedtuple('Force', ['x', 'y', 'z'])
        
    def get_force(self):
        pass  # Deferred to subclasses
        
    def add_step_listener(self, listener):
        self.step_listeners.append(listener)

    def step(self, dt_usec):
        """ Apply the force to the podand notify our listeners """
        force = self.get_force()
        self.sim.pod.apply_force(force)
        for step_listener in self.step_listeners:
            step_listener.step_callback(self, [force])
            
            
class LateralStabilityForce(ForceExerter):
    
    def __init__(self, sim, config):
        ForceExerter.__init__(self, sim, config)
        self.name = 'F_lateral_stability'

        self.damping_coefficient = Units.SI(self.config.damping_coefficient)

    def get_force(self):
        """ Get x force (drag -- return a negative number) provided by the lateral stability wheels. """
        # Note: You can get pod velocity/acceleration/position using e.g. self.sim.pod.velocity (see pod.py __init__() for vars)
        x = - ( self.damping_coefficient * self.sim.pod.velocity )
        y = 0 # No y force
        z = 0 # No z force
        return self.data(x, y, z)
        
        
class LandingGearForce(ForceExerter):
    
    def __init__(self, sim, config):
        ForceExerter.__init__(self, sim, config)
        self.name = 'F_landing_gear'
        
    def get_force(self):
        return self.data(0.0, 0.0, 0.0)
        

class GimbalForce(ForceExerter):
    
    def __init__(self, sim, config):
        ForceExerter.__init__(self, sim, config)
        self.name = 'F_gimbals'

    def get_force(self):
        """ Get x force provided by the hover engines. Note that this does NOT include force provided by gimbaling. """
        # @todo: decide whether or not we want to have gimbaling provide x force and lift for 4 of the engines, or to do x force (drag) for all engines in force_hover_engines.py
        return self.data(0.0, 0.0, 0.0)
        
        
class HoverEngineForce(ForceExerter):
    
    def __init__(self, sim, config):
        ForceExerter.__init__(self, sim, config)
        self.name = 'F_hover_engines'

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
        p1 = np.exp(self.lift_b * height)
        p2 = np.arctan(self.lift_c * (velocity + self.lift_k * rpm))
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
        # x = - coeff * (-np.exp(-.16*velocity)+1) * (1.6*np.exp(-0.2*velocity) + 1)  # NOTE: This doesn't work -- for some reason all the parens below are necessary
        x = - (height*(o2) + o1) * (-(np.exp(-0.16*velocity))+1)*((1.6*(np.exp(-0.02*velocity))+1))

        #print "Calculated he drag (1 engine) at height {} and velocity {}: {}".format(height, velocity, x)

        # @todo: is the drag for a single hover engine or all 8? 
        return self.data(8*x, 0, 8*z) # *8 because 8 hover engines

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
        
        
class AeroForce(ForceExerter):
    """ Applies aero drag to the pod """
    
    def __init__(self, sim, config):
        ForceExerter.__init__(self, sim, config)
        self.name = 'F_aero'

        # @see http://www.softschools.com/formulas/physics/air_resistance_formula/85/
        self.air_resistance_k = Units.SI(self.config.air_density) * self.config.drag_coefficient * Units.SI(self.config.drag_area) / 2
        
    def get_force(self):
        """ Get the drag force (based on pod velocity, negative in the x direction since it's drag) """
        x = -self.air_resistance_k * self.sim.pod.velocity ** 2
        y = 0 # No y force. y force isn't used in the simulator right now
        z = 0 # No z force for aero
        return self.data(x, y, z)
    
    
class BrakeForce(ForceExerter):
    
    def __init__(self, sim, config):
        ForceExerter.__init__(self, sim, config)
        self.name = 'F_brakes'

    def get_force(self):
        """ Get x force provided by the brakes. """
        # @todo: make this work. Probably need to go through self.sim to get pod velocity, etc. 

        """
        # Numerical simulation run at 6 different velocities -- see Keith's graph 
        # A34 data -- drag is for both brakes, lift is for one brake. Force_y has to do with the difference in force due to magnetic interactions and can be disregarded
        v = self.sim.pod.velocity
        air_gap = .024  # Should be self.sim.pod.brakes.gap, or brakes[i].gap if we're using an array of brakes, which we probably will
        
        # Fdrag(v) = gap_coefficient * (-e^(-.3*v)+1)*(1.5*e^(-.02*v)+1)
        # gap_coefficient = 5632e^-202gap
        
        # @todo: Either the drag force or the lift force is for a single brake, the other is for both. Which is which? 
        gap_coefficient = 5632 * np.exp(-202 * air_gap)
        f_drag = gap_coefficient * (-np.exp(-.3*v) + 1) * (1.5 * np.exp(-.02*v)+1)
        #print "Brake drag at air gap {}: {}".format(air_gap, -f_drag)
        """

        #f_drag = self.sim.brake_1.drag_force * 2  # *2 for both brakes. Just testing right now
        
        f_drag = self.sim.pod.brakes.get_drag() 
               
        return self.data(f_drag, 0, 0)

