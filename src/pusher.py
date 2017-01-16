#!/usr/bin/env python
# coding=UTF-8

# File:     pusher.py
# Purpose:  Pusher-related classes and time/acceleration/speed/position info
# Author:   Ryan Adams (@ninetimeout)
# Date:     2016-Dec-17

# NOTE: Please add your name to 'Author:' if you work on this file. Thanks!

# Note: all units are SI: meters/s^2, meters/s, and meters. Time is in microseconds (?)

from __future__ import division

from collections import namedtuple
from units import Units
import logging


class Pusher:
    
    def __init__(self, sim, config):
         
        self.sim = sim
        self.config = config        

        self.logger = logging.getLogger("Pusher")

        # State Machine (HOLD, PUSH, COAST, BRAKE, DONE)
        self.state = 'HOLD'
        self.coast_timer = 0
        
        # Configuration (these are defaults -- you can also set these directly at some later point)
        self.max_velocity = Units.SI(config.max_velocity)        # meters per second
        self.push_end_position = Units.SI(config.push_end_position)  # meters -- provided by spacex
        self.push_force = Units.SI(config.push_force)            # Newtons -- 350 kg * 2.4G (23.53596) = 8200 N
        self.coast_time_usec = Units.SI(config.coast_time)       # Note: the pusher will not likely disconnect during coast due to drag from the pod

        self.data = namedtuple('Force', ['x', 'y', 'z'])
    
    # -------------------------
    # Simulation methods
    # -------------------------

    def step(self, dt_usec):
        """ Handle the pusher state machine and simulation interactions """

        if self.state == "HOLD":
            pass
        elif self.state == "PUSH":
            if self.sim.pod.velocity < self.max_velocity and self.sim.pod.position <= self.push_end_position:
                self.sim.pod.apply_force( self.data(self.push_force, 0, 0) )
            else:
                if self.sim.pod.velocity >= self.max_velocity:
                    self.logger.info("Pusher reached max velocity of {} m/s".format(self.max_velocity))
                if self.sim.pod.position >= self.push_end_position:
                    self.logger.info("Pusher reached push end position of {} m (pod velocity was {:.2f} m/s)".format(self.push_end_position, self.sim.pod.velocity))
                self.set_state("COAST")
        elif self.state == "COAST":
            if self.coast_timer > self.coast_time_usec:
                self.set_state("BRAKE")

                # TESTING ONLY
                self.sim.pod.brakes._move_to_gap_target(.0025)  # Stop just after push
                
                self.coast_timer = 0
            else:
                self.coast_timer += dt_usec
        elif self.state == "BRAKE":
            # Note: pusher is disconnected from the pod at start of braking, because there will almost 
            # certainly be drag forces that keep the pod against the pusher during pusher coast. 
            self.disconnect_pod()
            self.set_state("DONE")  # just 'stop' immediately because we don't care about the pusher after it disconnects
        elif self.state == "DONE":
            pass   # Not much to do, just state that we're done
        else:
            raise Exception("Unknown state {}".format(self.state))
    
    def set_state(self, state):
        old_state = self.state
        self.state = state
        self.logger.info("Pusher entered {} state (from {})".format(self.state, old_state))
    
    # -------------------------
    # Control hooks
    # -------------------------
    
    def start_push(self):
        self.set_state("PUSH")
                   
    def disconnect_pod(self):
        self.sim.pod.disconnect_pusher()
        self.pod = None

if __name__ == "__main__":

    import argparse
    import datetime
    
    # Command line parsing
    import argparse
    parser = argparse.ArgumentParser(description="rPod Simulation")
    parser.add_argument('configfile', metavar='config', type=str, nargs='?', default="None",
        help='Simulation configuration file(s)')
    args = parser.parse_args()
    
    if args.configfile is not None:
        sim_config = Config()
        sim_config.loadfile(args.configfile)

    # Setup the simulator and elements
    sim = Sim(sim_config.sim)
    pusher = sim.pusher

    pusher.connect_pod(sim.pod)
    
    parser = argparse.ArgumentParser(description="Pusher simulation")
    parser.add_argument('-s', '--fixed_timestep_usec', help="Timestep of the simulation in microseconds", default=100000, required=False)

    parser.add_argument('-f', '--force', help="Force applied to the pod during push, in Newtons", default=8000, required=False)
    parser.add_argument('-m', '--max_v', help="Maximum push velocity in m/s", default=150, required=False)
    parser.add_argument('-c', '--coast', help="Coast time in microseconds", default=1000000, required=False)
    # @todo: For testing purposes only -- change over to generate as many as needed based on conditions if not provided
    parser.add_argument('-n', '--n_records', help="Number of records to generate", default=1001, required=False)
    args = parser.parse_args()
    
    # Pusher setup
    pod = Pod()
    pusher = Pusher()
    pusher.connect_pod(pod)
    
    pusher.push_force = float(args.force)
    pusher.coast_time_usec = float(args.coast)
    pusher.max_velocity = float(args.max_v)

    # Simulation settings
    fixed_timestep_usec = int(args.fixed_timestep_usec)
    
    # Start pushing right at the beginning. Could set up a wait before it, but not right now
    pusher.start_push()
    
    # test simulation -- Does a push/coast/brake cycle 
    print "{},{},{},{},{}".format("t_usec","pod_acceleration","pod_velocity","pod_position","processing_usec") # Header
    for i in xrange(int(args.n_records)):
        t = i * fixed_timestep_usec  # Note: need to offset -- what we're printing is *after* the step
        start = datetime.datetime.now()
        duration_usec = datetime.datetime.now() - start
        print "{},{},{},{},{}".format(t, pod.acceleration, pod.velocity, pod.position, duration_usec.microseconds)        
        pusher.step(fixed_timestep_usec)
        pod.step(fixed_timestep_usec)
