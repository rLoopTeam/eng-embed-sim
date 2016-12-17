#!/usr/bin/env python
# coding=UTF-8

# File:     battery.py
# Purpose:  Battery-related classes
# Author:   Ryan Adams
# Date:     2016-Dec-16

from power import PowerSource

# @todo: specify values for configuration -- should be able to be taken from a battery data sheet?

class Battery(PowerSource):
    
    def __init__(self, battery_config):
        # @todo: Check the configuration for properly ranged values (e.g. capacity_amp_hrs > 0)
        # NOTE: ALL variables that will be used in this class must be initialized here so that reset() will work.
        self.config = battery_config
        self.charge_amp_hrs = battery_config.get('initial_charge_amp_hrs', 0)   # Get the initial charge from the battery config

    def reset(self):
        # Reset everything to the original values
        self.__init__(self.config)
        
    def drain(self, amps, dt_usec):
        """ Drain the number of amps for the specified amount of time """
        # @todo: change this to a real equation
        # NOTE: Multiplying by 1.0 forces a float value, which we want (python idiosyncracy)
        self.charge_amp_hrs -= 1.0 * amps * dt_usec / (1000000 * 3600)  # amps times hours
        
    def charge(self, amps, dt_usec):
        """ Increase the battery charge """
        pass
        
    def set_charge(self, charge_amp_hrs):
        """ Set the charge amount directly """
        self.charge_amp_hrs = charge_amp_hrs
        
    def get_charge(self):
        """ Get the current charge (in amp hours?) """
        return self.charge_amp_hrs
        
    def get_charge_pct(self):
        """ Calculate the percent charge """
        # @todo: change this to a reql equation
        return self.charge_amp_hrs / self.config['capacity_amp_hrs']
        
        
if __name__ == "__main__":
    """
    Command line utility to output battery charge info with timestamp
    """

    import argparse
    import datetime
    
    parser = argparse.ArgumentParser(description="Battery code and demonstrator")
    parser.add_argument('-s', '--fixed_timestep_usec', help="Timestep of the simulation in microseconds", required=False)
    parser.add_argument('-n', '--n_records', help="Number of records to generate", required=False)
    parser.add_argument('-c', '--capacity_amp_hrs', help="Capacity of the battery in amp-hours", required=False)
    parser.add_argument('-i', '--initial_charge_amp_hrs', help="Initial charge of the battery in amp-hours", required=False)
    parser.add_argument('-a', '--max_amps', help="Maximum amperage that can be supplied by the battery", required=False)
    parser.add_argument('-d', '--drain_amps', help="Rate to drain the battery (amps?)", required=False)
    args = parser.parse_args()
    
    battery_config = {
        'capacity_amp_hrs': float(args.capacity_amp_hrs or 10000),
        'initial_charge_amp_hrs': float(args.initial_charge_amp_hrs or 10000),
        'max_amps': float(args.max_amps or 20)
    }
    
    # Create a battery
    b = Battery(battery_config)
    
    # Simulation settings
    fixed_timestep_usec = int(args.fixed_timestep_usec or 1000000)
    drain_amps = 5
    
    # test simulation
    print "{},{},{},{}".format("t_usec","charge_amp_hrs","charge_pct","processing_usec") # Header
    for i in xrange(int(args.n_records) or 1000):
        t = i * fixed_timestep_usec
        start = datetime.datetime.now()
        b.drain(drain_amps, fixed_timestep_usec)
        duration_usec = datetime.datetime.now() - start
        print "{},{},{},{}".format(t, b.get_charge(), b.get_charge_pct(), duration_usec.microseconds)
        
        