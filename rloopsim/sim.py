#!/usr/bin/env python
# coding=UTF-8

# File:     sim.py
# Purpose:  Physics and controls (software-in-the-loop) simulation for the rLoop pod
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2016-Dec-28


import os
import errno    
import time
import logging

from units import *
from config import Config
from timers import TimeDialator

from pod import Pod
from pusher import Pusher
from track import Track

from sensor_laser_contrast import *
from sensor_laser_dist import *
from sensor_laser_opto import *
from sensor_accel import *

from networking import PodComms

from fcu import Fcu

import threading

    # Testing
from sensor_laser_opto import *
from sensors import *   # @todo: move this to the top once we're done testing


class Sim(object):
    
    def __init__(self, config, working_dir=None):
        self.logger = logging.getLogger("Sim")

        self.logger.info("Initializing simulation")
        
        # Config
        self.config = config
        
        # Working directory (for csv files and whatnot)
        if working_dir is not None: 
            self.set_working_dir(working_dir)

        self.logger.info("Working directory is {} ({})".format(self.config.working_dir, os.path.join(os.getcwd(), self.config.working_dir)))
        
        self.ensure_working_dir()

        # Simulator control
        self.step_listeners = []  # For in-sim control (per step)
        self.end_conditions = []
        self.end_listeners = []
        
        # Pre and post 
        self.preprocessors = []
        self.postprocessors = []

        # Time
        self.fixed_timestep_usec = Units.usec(config.fixed_timestep)  # Convert to usec
        self.time_dialator = TimeDialator(self)  # We're going to step this

        # Components
        self.pusher = Pusher(self, self.config.pusher)
        self.track = Track(self, self.config.track)
        self.pod = Pod(self, self.config.pod)      
        #self.fcu = Fcu(self, self.config.fcu)  

        # Component setup

        # Set the initial pusher position to meet the pusher plate
        # @todo: should we set this somewhere else? Like in a run controller? 
        self.pusher.position = self.pod.pusher_plate_offset

        # Sensors
        self.sensors = {}
        self.sensors['pod'] = PodSensor(self, self.config.sensors.pod)
        self.sensors['pod'].add_step_listener( SensorCsvWriter(self, self.config.sensors.pod) )

        # - Accelerometers
        self.sensors['accel'] = []
                
        for idx, sensor_config in self.config.sensors.accel.iteritems():
            # Note: we need to create a Config object here because Config does not currently handle lists very well...
            self.sensors['accel'].append(Accelerometer(self, Config(sensor_config)))
            sensor = self.sensors['accel'][idx]
            sensor.add_step_listener(AccelerometerTestListener(self, sensor.config))
            sensor.add_step_listener(SensorCsvWriter(self, sensor.config))
            #sensor.add_step_listener(SensorRawCsvWriter(self, sensor.config))
        
        # - Laser Contrast Sensors
        self.sensors['laser_contrast'] = []
        for idx, sensor_config in self.config.sensors.laser_contrast.iteritems():
            self.sensors['laser_contrast'].append(LaserContrastSensor(self, Config(sensor_config)))
            sensor = self.sensors['laser_contrast'][idx]
            #sensor.add_step_listener(LaserContrastTestListener(self, sensor.config))  # For debugging
            sensor.add_step_listener(SensorCsvWriter(self, sensor.config))
            #sensor.add_step_listener(SensorRawCsvWriter(self, sensor.config))  # These don't have 'raw' values since they just call an interrupt

        # - Laser Opto Sensors (height and yaw)
        self.sensors['laser_opto'] = []
        for idx, sensor_config in self.config.sensors.laser_opto.iteritems():
            self.sensors['laser_opto'].append(LaserOptoSensor(self, Config(sensor_config)))
            sensor = self.sensors['laser_opto'][idx]
            #sensor.add_step_listener(LaserOptoTestListener(self, sensor.config))  # For debugging
            sensor.add_step_listener(SensorCsvWriter(self, sensor.config))
            #sensor.add_step_listener(SensorRawCsvWriter(self, sensor.config))   
        
        # - Laser Distance Sensor
        self.sensors['laser_dist'] = LaserDistSensor(self, Config(self.config.sensors.laser_dist))
        sensor = self.sensors['laser_dist']
        sensor.add_step_listener(SensorCsvWriter(self, sensor.config))
        #sensor.add_step_listener(SensorRawCsvWriter(self, sensor.config))

        # - Brake Sensors: MLP, limit switches (for both)
        pass
        
        # Networking
        self.comms = PodComms(self, self.config.networking)
        self.add_end_listener(self.comms)

        # FCU (!)
        if self.config.fcu.enabled:
            self.fcu = Fcu(self, self.config.fcu)
            self.add_end_listener(self.fcu)
        else:
            # @todo: will this have any side effects (e.g. not having an fcu?)
            self.logger.info("Not initializing FCU because it is disabled via config.")


        # Initial setup
        # @todo: write a method by which we can maybe control the push from the ground station or rpod_control vb.net app
        # @todo: write a means by which we can start the push some configurable amount of time after the pod enters READY state
        #self.pusher.start_push()  # Only for testing

        # Volatile
        self.elapsed_time_usec = 0
        self.n_steps_taken = 0
        
        # Testing laser opto sensor class
        # self.laser_opto_sensors = LaserOptoSensors(self, self.config.sensors.laser_opto)
        

        #self.pod_sensor_writer.pause()  # Paused for use in the gui

        # Testing brakes  (pod now has brakes)
        #from brakes import Brake
        #self.brake_1 = Brake(self, None)
        #self.brake_1.gap = 0.025 # Set it to test forces
        
        # End condition checker (to stop the simulation)
        self.add_end_condition(SimEndCondition())

        # Testing run controller (with pod state machine control)
        self.add_step_listener(StateMachineRunController())
        
        # Handle data writing
        # @ todo: handle data writing. Note: Each sim instance should be handed a directory to use for writing data
    
    @classmethod
    def load_config_files(cls, config_files):
        """ Load one or more config files (later files overlay earlier ones) """
        
        config = Config()
        for configfile in config_files:
            # Note: each file loaded by the config will overlay on the previously loaded files
            config.loadfile(configfile)
        return config.sim

    def set_working_dir(self, working_dir):
        """ Set our working directory (for file writing and whatnot) """
        self.config.working_dir = working_dir
    
    def data_logging_enabled(self, data_writer, sensor):
        """ Tell data writers whether or not to log data (e.g. csv writers) """
        # @todo: write something that gets a value from runtime config
        # @todo: write something that turns data logging on and off based on FCU state (assuming the FCU is enabled)
        # @todo: potentially turn on or off based on sensor, writer type, or a combination of the two
        return False  # Turn data logging off for now

    def step(self, dt_usec):        

        # Step the pusher first (will apply pressure and handle disconnection)
        self.pusher.step(dt_usec)

        # Step the pod (will handle all other forces and pod physics)
        self.pod.step(dt_usec)
        
        # Step the sensors
        for sensor in self.sensors.values():
            # Some of our sensors are lists of sensors
            if isinstance(sensor, list):
                for s in sensor:
                    s.step(dt_usec)        
            else:
                sensor.step(dt_usec)

        # Step the time dialator to keep our timers in sync
        self.time_dialator.step(dt_usec)
        if self.n_steps_taken % 500 == 0:
            self.logger.debug("Time dialation factor is {} after {} steps".format(self.time_dialator.dialation, self.n_steps_taken))

            info = {
                'psa': self.pusher.acceleration,
                'psv': self.pusher.velocity,
                'psp': self.pusher.position,
                'pda': self.pod.acceleration,
                'pdv': self.pod.velocity,
                'pdp': self.pod.position,
            }
            self.logger.debug("Pusher avp:  {psa}  {psv}  {psp};  Pod avp:  {pda}  {pdv}  {pdp}".format(**info))

        self.elapsed_time_usec += dt_usec
        self.n_steps_taken += 1

        for step_listener in self.step_listeners:
            step_listener.step_callback(self)

    def run_threaded(self):
        """ Run the simulator in a thread and return the thread (don't join it here) """
        
        t = threading.Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return t  # Return the thread, but don't join it (the caller can join if they want to)

    def run(self):

        self.logger.info("Starting simulation")

        self.end_flag = False
        sim_start_t = time.time()
        
        # Notify preprocessors
        for processor in self.preprocessors:
            processor.process(self)
        
        # Networking
        self.comms.run_threaded()   # Start the network node listeners

        # FCU
        if self.config.fcu.enabled:
            self.fcu.run_threaded()

        while(True):

            # Check our end listener(s) to see if we should end the simulation (e.g. the pod has stopped)
            for listener in self.end_conditions:
                if listener.is_finished(self):
                    self.end_flag = True
            
            if self.end_flag:
                # Notify our 'finished' listeners and break the loop
                for end_listener in self.end_listeners:
                    end_listener.end_callback(self)

                break
            
            self.step(self.fixed_timestep_usec)


        sim_end_t = time.time()
        sim_time = sim_end_t - sim_start_t
        #print "LaserOptoTestListener: gap sensor took {} samples that were within a gap.".format(self.lotl.n_gaps)
        self.logger.info("Simulated {} steps/{} seconds in {} actual seconds.".format(self.n_steps_taken, self.elapsed_time_usec/1000000, sim_time))

        # Notify postprocessors
        for processor in self.postprocessors:
            processor.process(self)

    def add_step_listener(self, listener):
        """ 
        Register a listener that will be called every step. 
        A step listener can be any class that implements the following method:
        - step_callback(sim)
        """
        self.step_listeners.append(listener)    

    def add_end_condition(self, listener):
        """ Add a listener that will tell us if we should end the simulator """
        self.end_conditions.append(listener)
    
    def add_end_listener(self, listener):
        """ Add a listener for when we've ended the sim """
        self.end_listeners.append(listener)

    def add_preprocessor(self, processor):
        self.preprocessors.append(processor)
        
    def add_postprocessor(self, processor):
        self.postprocessors.append(processor)
    
    def ensure_working_dir(self):
        """ Ensure existence of base directory for data storage """
        # @todo: Log the error/exception if there is one
        # Try to make the directory(s)        
        
        path = self.config.working_dir
        
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


class StateMachineRunController(object):
    """ Control the FCU state and pusher for a simulated run """

    def __init__(self):
        self.logger = logging.getLogger("StateMachineRunController")
        self.started = False
        self.pushed = False

    def setup_mission_profile(self):
        pass

    def step_callback(self, sim):
        POD_STATE__IDLE = 2
        POD_STATE__READY = 7

        # Move to ready state once we're in Idle
        if not self.started:
            if sim.fcu.get_sm_state() == POD_STATE__IDLE:
                self.logger.info("StateMachineRunController moving FCU to POD_STATE__READY")
                sim.fcu.force_ready_state()
                self.started = True

        # If we're in READY state, go ahead and start the push
        elif not self.pushed:  # elif to give the FCU a chance to get to ready state
            if sim.fcu.get_sm_state() == POD_STATE__READY:
                self.logger.info("StateMachineRunController signaling pusher to start push")
                sim.pusher.start_push()
                self.pushed = True


class SimEndCondition(object):

    def __init__(self):
        self.logger = logging.getLogger("SimEndListener")
        self.pushed = False
        
    def is_finished(self, sim):

        # Check to see if we should end the sim

        # If we've stopped (after being pushed)
        if sim.pod.velocity >= 0.0001:
            self.pushed = True  # set pushed to true when we've moved some
        elif self.pushed == True:  # Next time around, if we've been pushed, check to see if we've stopped.
            if sim.pod.velocity <= 0.001:  # arrg floating points
                self.logger.info("Ending simulation because reasons")
                return True

        # If we've hit the wall...
        if sim.pod.position >= sim.track.length:
            self.logger.info("The pod has destroyed the track and everything else within a 10 mile radius.")
            return True

        return False


if __name__ == "__main__":
    import sys
    import logging
    import logging.config
    import yaml

    #from debug import stacktracer
    #stacktracer.trace_start("trace.html",interval=5,auto=True) # Set auto flag to always update file!

    with open('conf/logging.conf') as f:  # @todo: make this work when run from anywhere (this works if run from top directory)
        logging.config.dictConfig(yaml.load(f))
        
    test_logger = logging.getLogger("NetworkNode")
    print(test_logger.__dict__)

    from config import *

    import pprint
    
    import argparse
    parser = argparse.ArgumentParser(description="rPod Simulation")
    parser.add_argument('configfile', metavar='config', type=str, nargs='+', default="None",
        help='Simulation configuration file(s) -- later files overlay on previous files')
    args = parser.parse_args()

    # Note: 'configfile' is a list of one or more config files. Later files overlay previous ones. 
    sim = Sim( Sim.load_config_files(args.configfile), '../eng-embed-sim-data/test')
    #t = sim.run_threaded()
    #t.join()
    
    sim.run()
    
    # Keep the script alive until we're done (works with both threading and non-threading cases)
    while True:
        if sim.end_flag:
            sys.exit(0)

        try:
            time.sleep(0.1)
        except:
            #stacktracer.trace_stop()
            sys.exit(0)
    
    """
    sim_config = Config()
    for configfile in args.configfile:
        sim_config.loadfile(configfile)
    
    #pprint.pprint(sim_config)
    
    sim = Sim(sim_config.sim)

    import threading
    t = threading.Thread(target=sim.run, args=())
    t.start()
    t.join()
    #sim.run()

    """