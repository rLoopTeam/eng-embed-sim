#!/usr/bin/env python

from units import Units

class HoverEngineForce:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config 

    def get_force(self):
        """ Get x force provided by the hover engines. Note that this does NOT include force provided by gimbaling. """
        # @todo: decide whether or not we want to have gimbaling provide x force and lift for 4 of the engines, or to do x force (drag) for all engines here...
        return 0.0
        
    def get_lift(self):
        """ 
        Get lift provided by hover engines """
        return 0.0
        
        
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
    