#!/usr/bin/env python

# @todo: This is a sketch. Maybe we need to store temperature? Variable values/names/units can change.

class HeatSource:
    def __init__(self):
        self.stored_heat_energy = 0.  # @todo: what units to use for heat? Also, what about ambient temp? 
    
    def generate(self, heat_joules, dt_usec):
        self.heat_energy += heat_joules * (dt_usec / 1000000) 


class HeatSink:
    
    def __init__(self):
        self.capacity = 0.     # @todo: determine units
        self.sink_rate = 0.1   # @todo: determine units of measurement here -- watts per second? 

        self.stored_heat_energy = 0.  # @todo: what about ambient heat? 
        
    def offload(self, source, heat_joules, dt_usec):
        """ Offload as much heat as possible and reduce the heat in the source """
        source.stored_heat_energy = ...
        
    
if __name__ == "__main__":

    # Simple example
    source = HeatSource()
    sink = HeatSink()
    
    dt_usec = 1000000  # 1 second
    
    heat_to_generate_in_some_reasonable_units = 1.
    
    source.generate(heat_to_generate_in_some_reasonable_units, dt_usec)
    sink.draw(source, dt_usec)
    
    print source.stored_heat_energy  # Should be less than we generated
    print sink.stored_heat_energy    # Should be more than we started with 