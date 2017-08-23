#!/usr/bin/env python
# coding=UTF-8

# File:     pusher.py
# Purpose:  Pusher-related classes and time/acceleration/speed/position info
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2016-Dec-17

# NOTE: Please add your name to 'Author:' if you work on this file. Thanks!

# Note: all units are SI: meters/s^2, meters/s, and meters. Time is in microseconds (?)

from __future__ import division

from collections import namedtuple
from units import Units
import logging


class Pusher(object):
    
    def __init__(self, sim, config):
         
        self.sim = sim
        self.config = config        

        self.logger = logging.getLogger("Pusher")

        # State Machine (HOLD, PUSH, COAST, BRAKE, DONE)
        self.state = 'HOLD'
        self.coast_timer = 0.0

        # Physics
        self.acceleration = 0.0
        self.velocity = 0.0
        self.position = 0.0
        self.last_acceleration = 0.0
        self.last_velocity = 0.0
        self.last_position = 0.0

        self.push_time_sec = 0.0
        self.elapsed_time_sec = 0.0

        # Configuration (these are defaults -- you can also set these directly at some later point)
        self.max_push_velocity = Units.SI(config.max_push_velocity)        # meters per second
        self.max_push_time = Units.SI(config.max_push_time)  # @todo: test this -- seconds? 
        self.push_end_position = Units.SI(config.push_end_position)  # meters -- provided by spacex
        #self.push_force = Units.SI(config.push_force)            # Newtons -- 350 kg * 2.4G (23.53596) = 8200 N
        self.push_accel = Units.SI(config.push_accel)              # m/s^2
        self.brake_decel = Units.SI(config.brake_decel)
        self.coast_duration = Units.SI(config.coast_duration)       # Note: the pusher will not likely disconnect during coast due to drag from the pod

        # @todo: change this to reasonable data about our pusher
        self.data = namedtuple('Force', ['x', 'y', 'z'])  

        self.debug_print_step = False
    
    def update_physics(self, dt_usec):
        """ Update the pusher physics based on the acceleration (set elsewhere) """

        # Save off our last values
        self.last_acceleration = self.acceleration
        self.last_velocity = self.velocity
        self.last_position = self.position
        
        t_sec = dt_usec / 1000000.0
        
        # v*t + 1/2*a*t^2
        self.position += self.velocity * t_sec + 0.5 * self.acceleration * (t_sec ** 2)
        
        # vf = v0 + at
        self.velocity = self.velocity + self.acceleration * t_sec


    # -------------------------
    # Simulation methods
    # -------------------------

    def step(self, dt_usec):
        """ Handle the pusher state machine and simulation interactions """

        # @todo: update this to use velocity control (or something that approximates it -- limited accel?)
        # @todo: allow disconnect/reconnect of pod based on relative position
            # Need to be able to have the pusher 'take over' the accel/pos/velocity of the pod
            # Maybe extract the physics calculation and allow switching between the physics of the pusher and that of the pod? 

        if self.state == "HOLD":
            pass

        elif self.state == "PUSH":
            
            # Calculate and set our acceleration
            # Based on push_accel, max_push_velocity, and max_push_distance, and maybe max_push_time
            # Maybe also enact state transition if we've reached max distance or time

            # Note: the pod will update itself based on us; we don't need to tell it anything

            if self.position >= self.push_end_position:                
                # We've reached the end of the push (by distance limit)
                self.logger.info("Pusher reached push end position of {} m (pusher velocity was {:.2f} m/s)".format(self.push_end_position, self.velocity))
                self.set_state("COAST")

            elif self.push_time_sec >= self.max_push_time:
                # We've reached the end of the push (by time limit)
                self.logger.info("Pusher reached max push time of {} seconds".format(self.max_push_time))
                self.set_state("COAST")

            elif self.velocity >= self.max_push_velocity:
                # We've reached max velocity limit, so don't accelerate any more
                self.logger.info("Pusher reached max velocity of {} m/s".format(self.max_push_velocity))
                self.acceleration = 0.0

            else:
                # We're pushing at our push acceleration
                self.acceleration = self.push_accel

            # Update physics
            self.update_physics(dt_usec)

            # Update our push time
            self.push_time_sec += dt_usec / 1000000.0

        elif self.state == "COAST":

            if self.coast_timer > self.coast_duration:
                self.set_state("BRAKE")

                # TESTING ONLY
                #self.sim.pod.brakes._move_to_gap_target(.0025)  # Stop just after push
                
                self.coast_timer = 0.0  # just reset
            else:
                self.coast_timer += dt_usec / 1000000.0

            # Update physics
            self.update_physics(dt_usec)

        elif self.state == "BRAKE":
            # @todo: handle braking physics (set braking acceleration)
            
            if self.velocity <= 0.0001:   # m/s
                self.velocity = 0.0
                self.set_state("STOPPED")  # just 'stop' immediately because we don't care about the pusher after it disconnects
            else:
                self.acceleration = self.brake_decel

            # Update physics
            self.update_physics(dt_usec)

        elif self.state == "STOPPED":
            pass   # Not much to do, we're done

        else:
            raise Exception("Unknown state {}".format(self.state))

        self.elapsed_time_sec += dt_usec / 1000000.0

        # Print our step if requested
        if self.debug_print_step:
            info = {
                't': self.elapsed_time_sec,
                'state': self.state,
                'a': self.acceleration,
                'v': self.velocity,
                'p': self.position,
            }
            print("{t} {state} {a} {v} {p}".format(**info))

    
    def set_state(self, state):
        old_state = self.state
        self.state = state
        self.logger.info("Pusher entered {} state (from {})".format(self.state, old_state))
    

    # -------------------------
    # Control hooks
    # -------------------------
    
    def start_push(self):
        self.set_state("PUSH")
    
    def run_standalone(self, dt_usec):
        self.debug_print_step = True
        self.step(dt_usec)  # A step to get us started
        self.set_state("PUSH")
        while(self.state != "STOPPED"):
            self.step(dt_usec)
        self.step(dt_usec)  # A step to finish us off
        print("Done.")



if __name__ == "__main__":

    # @todo: update this to use 

    import argparse
    import datetime
    
    from config import Config

    # Command line parsing
    import argparse
    parser = argparse.ArgumentParser(description="SpaceX Pusher Simulation")
    parser.add_argument('configfile', metavar='config', type=str, nargs='?', default="None",
        help='Simulation configuration file(s)')
    args = parser.parse_args()
    
    if args.configfile is not None:
        sim_config = Config()
        sim_config.loadfile(args.configfile)

    # Setup the simulator and elements
    #sim = Sim(sim_config.sim)
    #pusher = sim.pusher
    pusher = Pusher(None, sim_config.sim.pusher)
    dt_usec = 100000
    pusher.run_standalone(dt_usec)


    #pusher.connect_pod(sim.pod)
    """ Pusher simulator (needs to be updated, but might be useful)
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
    """
