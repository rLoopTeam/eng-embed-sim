#!/usr/bin/env python

from pod import Pod
from tube import Tube
from pusher import Pusher
#from fcu import fcu

import os
import errno    
import time
import logging
from units import *
from config import Config

import threading

# Testing
from sensor_laser_opto import *
from sensors import *   # @todo: move this to the top once we're done testing


class SimRunner:
    """ Manages run of a single simulation """

    def __init__(self, sim_config_files, working_dir=None):
        self.logger = logging.getLogger("SimRunner")

        # Pre and post processors (for setting things up, making plots, etc.)
        # Note: these will get passed to the simulator to be handled
        self.preprocessors = []
        self.postprocessors = []

        # Load the config files. Successive files overlay on the previous config files
        self.sim_config = Config()
        for configfile in sim_config_files:
            # Note: each file loaded by the config will overlay on the previously loaded files
            self.sim_config.loadfile(configfile)

        # Decorate the config with our working directory (if we're overriding)
        if working_dir is not None:
            self.sim_config.sim.working_dir = working_dir
        self.working_dir = working_dir
        self.logger.info("Working directory is {} ({})".format(working_dir, os.path.join(os.getcwd(), working_dir)))
        
        # Turn threading on/off. NOTE: The only time to turn this off is for debugging purposes. Threading is required for timers and the FCU. 
        self._threaded = True
        
        
    def run(self):
        """ Run the simulation """
        
        # Make sure our working directory exists
        self.ensure_data_dir(self.sim_config.sim.working_dir)

        # Create the simulator
        self.sim = Sim(self.sim_config.sim)

        # Pass in our pre and post processors
        self.sim.preprocessors = self.preprocessors
        self.sim.postprocessors = self.postprocessors

        if self._threaded:
            t = threading.Thread(target=self.sim.run, args=())
            t.daemon = True
            t.start()
            t.join()
        else:
            sim.run()

    def _to_abspath(self, path):
        if os.path.isabs(path):
            # Absolute path
            return os.path.realpath(path)
        else:
            # Get the path relative to the directory above this one (the base path of the repo)
            return os.path.realpath(os.path.join(os.getcwd(), path))
    
    def ensure_data_dir(self, path):
        """ Ensure existence of base directory for data storage """
        # @todo: Log the error/exception if there is one
        # Try to make the directory(s)        
        print "Trying out path {}".format(path)
        print self.sim_config
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


class Sim:
    
    def __init__(self, config):
        self.logger = logging.getLogger("Sim")

        self.logger.info("Initializing simulation")
        
        self.config = config

        self.fixed_timestep_usec = Units.usec(config.fixed_timestep)  # Convert to usec

        self.pusher = Pusher(self, self.config.pusher)
        self.tube = Tube(self, self.config.tube)
        self.pod = Pod(self, self.config.pod)      
        #self.fcu = Fcu(self, self.config.fcu)  

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
        self.laser_opto_sensors = LaserOptoSensors(self, self.config.sensors.laser_opto)
        
        
        # Testing only
        """
        from sensor_laser_opto import LaserOptoSensor, LaserOptoTestListener
        self.laser_opto_1 = LaserOptoSensor(self, self.config.sensors.laser_opto_1)
        #self.laser_opto_1.register_step_listener(SensorConsoleWriter())  # Write data directly to the console
        self.lotl = LaserOptoTestListener()
        self.laser_opto_1.add_step_listener(self.lotl) 
        self.lofl = SensorCsvWriter(Config({'filename': "sensorcsvwriter_test1.csv"}))
        self.laser_opto_1.add_step_listener(self.lofl)
        """
        
        # Testing laser contrast sensor
        from sensor_laser_contrast import LaserContrastSensor, LaserContrastTestListener
        self.laser_contrast_1 = LaserContrastSensor(self, self.config.sensors.laser_contrast_1)
        self.lctl = LaserContrastTestListener()
        self.laser_contrast_1.add_step_listener(self.lctl)

        # Testing pod sensor
        self.pod_sensor = PodSensor(self, None)
        self.pod_sensor_writer = SensorCsvWriter(self, self.config.sensors.pod)
        self.pod_sensor.add_step_listener(self.pod_sensor_writer)

        #self.pod_sensor_writer.pause()  # Paused for use in the gui

        # Testing brakes  (pod now has brakes)
        #from brakes import Brake
        #self.brake_1 = Brake(self, None)
        #self.brake_1.gap = 0.025 # Set it to test forces
        
        # End condition checker (to stop the simulation)
        self.add_end_condition(SimEndCondition())
        
        # Handle data writing
        # @ todo: handle data writing. Note: Each sim instance should be handed a directory to use for writing data
    
    
    def step(self, dt_usec):        

        # Step the pusher first (will apply pressure and handle disconnection)
        self.pusher.step(dt_usec)

        # Step the pod (will handle all other forces and pod physics)
        self.pod.step(dt_usec)
        
        # Testing only
        
        self.pod_sensor.step(dt_usec)
        #self.fcu.step(dt_usec)
        #self.laser_opto_1.step(dt_usec)
        #self.logger.debug(list(self.laser_opto_1.pop_all()))
        self.laser_contrast_1.step(dt_usec)
        #self.brake_1.step(dt_usec)
        
        # Done testing
        
        self.elapsed_time_usec += dt_usec
        self.n_steps_taken += 1

    def run(self):
        self.logger.info("Starting simulation")
        
        finished = False
        sim_start_t = time.time()
        
        # Notify preprocessors
        for processor in self.preprocessors:
            processor.process(self)
        
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
        if sim.pod.position >= sim.tube.length:
            self.logger.info("Pod has destroyed the tube and everything within a 10 mile radius.")
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

    runner = SimRunner(args.configfile, 'data/test')
    t = runner.run_threaded()
    t.join()
    
    """
    sim_config = Config()
    for configfile in args.configfile:
        sim_config.loadfile(configfile)
    
    #pprint.pprint(sim_config)
    
    # print sim_config.sim.world.tube.length

    sim = Sim(sim_config.sim)

    import threading
    t = threading.Thread(target=sim.run, args=())
    t.start()
    t.join()
    #sim.run()

    """
