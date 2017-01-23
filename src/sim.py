#!/usr/bin/env python


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
from sensor_accel import *

from networking import PodComms

from fcu import Fcu

import threading

# Testing
from sensor_laser_opto import *
from sensors import *   # @todo: move this to the top once we're done testing


class Sim:
    
    def __init__(self, config, working_dir=None):
        self.logger = logging.getLogger("Sim")

        self.logger.info("Initializing simulation")
        
        # Config
        self.config = config
        
        # Working directory (for csv files and whatnot)
        if working_dir is not None: 
            self.set_working_dir(working_dir)

        # Time
        self.fixed_timestep_usec = Units.usec(config.fixed_timestep)  # Convert to usec
        self.time_dialator = TimeDialator(self)  # We're going to step this

        # Components
        self.pusher = Pusher(self, self.config.pusher)
        self.track = Track(self, self.config.track)
        self.pod = Pod(self, self.config.pod)      
        #self.fcu = Fcu(self, self.config.fcu)  

        # Sensors
        self.sensors = {}
        self.sensors['pod'] = PodSensor(self, self.config.sensors.pod)
        self.sensors['pod'].add_step_listener(SensorCsvWriter(self, self.config.sensors.pod))

        # - Accelerometers
        self.sensors['accel'] = []
        for i, sensor_config in enumerate(self.config.sensors.accel):
            # Note: we need to create a Config object here because Config does not currently handle lists very well...
            self.sensors['accel'].append(Accelerometer(self, Config(sensor_config)))
            self.sensors['accel'][i].add_step_listener(AccelerometerTestListener(self, self.sensors['accel'][i].config))
        
        # - Laser Contrast Sensors
        self.sensors['laser_contrast'] = []
        for i, sensor_config in enumerate(self.config.sensors.laser_contrast):
            self.sensors['laser_contrast'].append(LaserContrastSensor(self, Config(sensor_config)))
            self.sensors['laser_contrast'][i].add_step_listener(LaserContrastTestListener(self, self.sensors['laser_contrast'][i].config))

        # - Laser Opto Sensors (height and yaw)
        pass
        
        # - Other
        pass  # @todo: add in other sensors

        
        # Networking
        self.comms = PodComms(self, self.config.networking)

        # FCU (!)
        if self.config.fcu.enabled:
            self.logger.info("Initializing FCU")
            self.fcu = Fcu(self, self.config.fcu)
        else:
            # @todo: will this have any side effects (e.g. not having an fcu?)
            self.logger.info("Not initializing FCU because it is disabled via config.")


        # Initial setup
        self.pusher.start_push()

        # Volatile
        self.elapsed_time_usec = 0
        self.n_steps_taken = 0
        
        # Simulator control
        self.end_conditions = []
        
        # Pre and post 
        self.preprocessors = []
        self.postprocessors = []
        
        # Testing laser opto sensor class
        # self.laser_opto_sensors = LaserOptoSensors(self, self.config.sensors.laser_opto)
        

        #self.pod_sensor_writer.pause()  # Paused for use in the gui

        # Testing brakes  (pod now has brakes)
        #from brakes import Brake
        #self.brake_1 = Brake(self, None)
        #self.brake_1.gap = 0.025 # Set it to test forces
        
        # End condition checker (to stop the simulation)
        self.add_end_condition(SimEndCondition())
        
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
        
        self.elapsed_time_usec += dt_usec
        self.n_steps_taken += 1

    def run_threaded(self):
        """ Run the simulator in a thread and return the thread (don't join it here) """
        
        t = threading.Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return t  # Return the thread, but don't join it (the caller can join if they want to)

    def run(self):
        self.logger.info("Starting simulation")
        
        self.ensure_working_dir()

        self.logger.info("Working directory is {} ({})".format(self.config.working_dir, os.path.join(os.getcwd(), self.config.working_dir)))

        finished = False
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
                    finished = True
            
            if finished:
                break
            
            self.step(self.fixed_timestep_usec)


        sim_end_t = time.time()
        sim_time = sim_end_t - sim_start_t
        #print "LaserOptoTestListener: gap sensor took {} samples that were within a gap.".format(self.lotl.n_gaps)
        self.logger.info("Simulated {} steps/{} seconds in {} actual seconds.".format(self.n_steps_taken, self.elapsed_time_usec/1000000, sim_time))

        # Notify postprocessors
        for processor in self.postprocessors:
            processor.process(self)

        
    def add_end_condition(self, listener):
        """ Add a listener that will tell us if we should end the simulator """
        self.end_conditions.append(listener)
        
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
            self.logger.info("Pod has destroyed the track and everything else within a 10 mile radius.")
            return True

        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    from config import *

    import pprint
    
    import argparse
    parser = argparse.ArgumentParser(description="rPod Simulation")
    parser.add_argument('configfile', metavar='config', type=str, nargs='+', default="None",
        help='Simulation configuration file(s) -- later files overlay on previous files')
    args = parser.parse_args()

    # Note: 'configfile' is a list of one or more config files. Later files overlay previous ones. 
    sim = Sim( Sim.load_config_files(args.configfile), 'data/test')
    t = sim.run_threaded()
    t.join()
    
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
