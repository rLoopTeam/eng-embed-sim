#!/usr/bin/env python

# coding=UTF-8

# File:     battery.py
# Purpose:  Environment-related classes
# Author:   Ryan Adams (@ninetimeout)
# Date:     2016-Dec-17

# Sketch of the environment model

# What units to use for pressure? Atm/sec? Pascals/s? Probably want to standardize on SI...

class Environment: 
    """ Model of the environment. Acts as a heat sink (and heat source?), maybe among other things """
    
    def __init__(self, properties):
        self.properties = properties
        self.heatsink = HeatSink()
        self.pressure_in_appropriate_units = properties.initial_pressure_(some appropriate units)
        self.heatsink.temperature_degc = properties.initial_temperature_degc
        
    # Methods so that we can act like a heat sink. 
    # Should match the signatures of HeatSink (see heat.py)
    def offload_heat(self, heat_joules, dt_usec):
        self.heat_sink.offload_heat(heat_joules, dt_usec)
    
    def change_pressure(self, rate, dt_usec):
        # Note: rate can be positive or negative. 
        self.pressure_in_appropriate_units -= rate * dt_usec * 1000000 # Assuming rate is [something] per second
        self.heat_sink.sink_rate = # (some calculation based on our pressure -- sink rate reduces as pressure decreases. Just needs to be approximate)