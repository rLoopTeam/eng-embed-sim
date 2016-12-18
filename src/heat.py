#!/usr/bin/env python


class HeatSource:
    def __init__(self):
        self.temperature = 0.  # temperature of the heat source in C degrees
    
    def generate(self, heat_joules, dt_usec):
        self.heat_energy += heat_joules / (dt_usec / 1000000) 


class HeatSink:
    
    def __init__(self):
        self.heat_capacity = 0.     # Heat capacity of the environment in Joules/Celsius
        self.heat_transfer_rate = 0.1   # in Watts 
        self.pressure = 0.125 #in psi
        self.temperature = 0.  # @todo: what about ambient heat? 
        
    def offload(self, source, heat_joules, dt_usec):
        """ Reduce the temperature of the object """
        source.stored_heat_energy = ...
        
    
if __name__ == "__main__":
    # Simple example
    source = HeatSource()
    sink = HeatSink()
    
    dt_usec = 1000000  # 1 second
    
    temp_increase = 1. #in Celsius
    
    source.generate(temp_increase), dt_usec)
    sink.draw(source, dt_usec)
    
    print source.stored_heat_energy  # Should be less than we generated
    print sink.stored_heat_energy    # Should be more than we started with