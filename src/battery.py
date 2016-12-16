#!/usr/bin/env python

# File:     battery.py
# Purpose:  Battery-related classes
# Author:   Ryan Adams
# Date:     2016-Dec-16

from power import PowerSource

# @todo: specify values for configuration -- should be able to be taken from a battery data sheet?

class Battery(PowerSource):
    
    def __init__(self, battery_config):
        # @todo: Check the configuration for properly ranged values (e.g. capacity_amp_hrs > 0)
        self.config = battery_config
        self.charge_amp_hrs = battery_config.get('initial_charge_amp_hrs', 0)   # Get the initial charge from the battery config
        
    def drain(self, amps, dt_usec):
        """ Drain the number of amps for the specified amount of time """
        # @todo: change this to a real equation
        # NOTE: Multiplying by 1.0 forces a float value
        self.charge_amp_hrs -= 1.0 * amps * dt_usec / (1000000 * 3600)  # amps times hours
        
    def charge(self, amps, dt_usec):
        """ Increase the battery charge """
        pass
        
    def set_charge(self, charge_amp_hrs):
        """ Set the charge amount directly """
        pass
        
    def get_charge(self):
        """ Get the current charge (in amp hours?) """
        return self.charge_amp_hrs
        
    def get_charge_pct(self):
        """ Calculate the percent charge """
        # @todo: change this to a reql equation
        return self.charge_amp_hrs / self.config['capacity_amp_hrs']
        
        
if __name__ == "__main__":
    battery_config = {
        'capacity_amp_hrs': 10000,
        'initial_charge_amp_hrs': 10000
    }
    
    # Create a battery
    b = Battery(battery_config)
    
    # Simulation settings
    fixed_timestep_usec = 1000000
    drain_amps = 5
    
    # test simulation
    for i in xrange(1000):
        t = i * fixed_timestep_usec
        b.drain(drain_amps, fixed_timestep_usec)
        print "{},{},{}".format(t, b.get_charge(), b.get_charge_pct())
        
        