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
import logging.config
import yaml


from units import *
#from config import Config
from config import *

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
        
        # Control flags (these act as requests)
        self.end_flag = False
        self.paused_flag = False

        # Status vars (these indicate actual status)
        self.is_ready = False  # Simulation is ready to run
        self.is_ended = False  # Simulation has ended

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

        self.sensors['pusher'] = PusherSensor(self, self.config.sensors.pusher)
        self.sensors['pusher'].add_step_listener( SensorCsvWriter(self, self.config.sensors.pusher) )

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
        """
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
        """

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
        #self.add_end_condition(SimEndCondition())  # Currently disabled in favor of using the RunController
        
        # Handle data writing
        # @ todo: handle data writing. Note: Each sim instance should be handed a directory to use for writing data
    
        self.logger.info("Simulator initialized")
        self.is_ready = True

    @classmethod
    def load_config_files(cls, config_files):
        """ Load one or more config files (later files overlay earlier ones) """
        
        ymls = []
        for configfile in config_files:
            with open(configfile, 'rb') as f:
                ymls.append(yaml.load(f))
        merged = {}
        for yml in ymls:
            merged = yaml_merge(merged, yml)

        config = Config(merged)
        return config.sim

        #config = Config()
        #for configfile in config_files:
            # Note: each file loaded by the config will overlay on the previously loaded files
        #    config.loadfile(configfile)
        #return config.sim

    def set_working_dir(self, working_dir):
        """ Set our working directory (for file writing and whatnot) """
        self.config.working_dir = working_dir
    
    def data_logging_enabled(self, data_writer, sensor):
        """ Tell data writers whether or not to log data (e.g. csv writers) """
        # @todo: write something that gets a value from runtime config
        # @todo: write something that turns data logging on and off based on FCU state (assuming the FCU is enabled)
        # @todo: potentially turn on or off based on sensor, writer type, or a combination of the two
        return True  # Turn data logging off for now


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

            # Debugging
            self.logger.debug("Track DB {}".format(self.fcu.lib.u32FCU_FCTL_TRACKDB__Get_CurrentDB()))

            info = [
                #self.fcu.lib.u8FCU_FCTL_TRACKDB__Accel__Get_Use(),  # Deprecated
                self.fcu.lib.s32FCU_FCTL_TRACKDB__Accel__Get_Accel_Threshold_mm_ss(),
                self.fcu.lib.s16FCU_FCTL_TRACKDB__Accel__Get_Accel_ThresholdTime_x10ms(),
                self.fcu.lib.s32FCU_FCTL_TRACKDB__Accel__Get_Decel_Threshold_mm_ss(),
                self.fcu.lib.s16FCU_FCTL_TRACKDB__Accel__Get_Decel_ThresholdTime_x10ms(),
            ]
            self.logger.debug("Track DB: Accel: {}".format(info))

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

            try: 
                # Check our end listener(s) to see if we should end the simulation (e.g. the pod has stopped)
                for listener in self.end_conditions:
                    if listener.is_finished(self):
                        self.stop()
            
                if self.end_flag:
                    # Notify our 'finished' listeners and break the loop
                    for end_listener in self.end_listeners:
                        end_listener.end_callback(self)

                    break  # Break out of our run loop
                
                if not self.paused_flag:
                    # @todo: do we need to handle pausing on other threads? Time runner for instance? 
                    # @todo: Maybe implement a pause listener or something? 
                    self.step(self.fixed_timestep_usec)
            
            except KeyboardInterrupt:
                self.logger.info("Received KeyboardInterrupt -- stopping simulation.")
                self.stop()


        sim_end_t = time.time()
        sim_time = sim_end_t - sim_start_t
        #print "LaserOptoTestListener: gap sensor took {} samples that were within a gap.".format(self.lotl.n_gaps)
        self.logger.info("Simulated {} steps/{} seconds in {} actual seconds.".format(self.n_steps_taken, self.elapsed_time_usec/1000000, sim_time))

        # Notify postprocessors
        for processor in self.postprocessors:
            processor.process(self)

        self.is_ended = True

    def stop(self):
        self.logger.info("Stopping Simulation")
        self.end_flag = True  # Request that the sim stop

    def pause(self):
        # @todo: *** This needs more work -- need to pause all threads...
        self.logger.info("Simulation (not) paused")
        #self.paused_flag = True
        self.paused_flag = False  # Disabling this for now until we can work out pausing for all threads

    def resume(self):
        self.logger.info("Resuming simulation")
        self.paused_flag = False

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

        self.push_step_counter = 0
        self.ready_state_counter = 0

        # Do we want to automatically jump to ready state and push?
        self.wait_steps_push = 0  # number of steps to wait for the push after entering POD_STATE__READY

        self.jump_to_ready_state = True
        self.fake_accel_transition = False
        self.end_after_spindown = True

        self.sim_finished = False

        self.state = "INIT"

    def setup_mission_profile(self):
        pass

    def step_callback(self, sim):
        POD_STATE__INIT = 1
        POD_STATE__IDLE = 2
        POD_STATE__TEST_MODE = 3
        POD_STATE__DRIVE = 4
        POD_STATE__ARMED_WAIT = 5
        POD_STATE__FLIGHT_PREP = 6
        POD_STATE__READY = 7
        POD_STATE__ACCEL = 8
        POD_STATE__COAST_INTERLOCK = 9
        POD_STATE__BRAKE = 10
        POD_STATE__SPINDOWN = 11

        if self.state is "INIT":
            # Wait for the FCU to get to IDLE
            if sim.fcu.get_sm_state() == POD_STATE__IDLE:
                self.state = "IDLE"

        elif self.state is "IDLE":
            u8TrackIndex = 0
            u8Use = 1

            s32AccelThresh_mm_ss = 20
            u16AccelThresh_x10ms = 30
            s32DecelThresh_mm_ss = 21
            u16DecelThresh_x10ms = 31

            # FCU is in IDLE -- set our accel thresholding values
            """ # This didn't work -- probably need to set the header and handle CRC stuff -- see the RPOD_CONTROL for more detail
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Accel__Use(u8TrackIndex, u8Use);
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Accel__Threshold_mm_ss(u8TrackIndex, s32AccelThresh_mm_ss);
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Accel__Threshold_x10ms(u8TrackIndex, u16AccelThresh_x10ms);
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Decel__Threshold_mm_ss(u8TrackIndex, s32DecelThresh_mm_ss);
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Decel__Threshold_x10ms(u8TrackIndex, u16DecelThresh_x10ms);
            """
            # @todo: check that the values were set properly
            #sim.fcu.lib.vFCU_ACCEL_THRESH__Set_Accel_Threshold(s32AccelThresh_mm_ss, u16AccelThresh_x10ms);
            #sim.fcu.lib.vFCU_ACCEL_THRESH__Set_Decel_Threshold(s32DecelThresh_mm_ss, u16DecelThresh_x10ms);
            """
            DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Accel__Threshold_mm_ss(Luint8 u8TrackIndex, Lint32 s32Thresh_mm_ss);
            DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Accel__Threshold_x10ms(Luint8 u8TrackIndex, Luint16 u16Thresh_x10ms);
            DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Decel__Threshold_mm_ss(Luint8 u8TrackIndex, Lint32 s32Thresh_mm_ss);
            DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Decel__Threshold_x10ms(Luint8 u8TrackIndex, Luint16 u16Thresh_x10ms);

            //track system
            DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Time__Accel_Coast_x10ms(Luint8 u8TrackIndex, Luint32 u32Value);
            DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Time__Coast_Brake_x10ms(Luint8 u8TrackIndex, Luint32 u32Value);
            DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Time__Brake_Spindown_x10ms(Luint8 u8TrackIndex, Luint32 u32Value);
            """
            """
            sim:
                mission_profile:
                    selected_profile: 0
                    profiles:
                      0:
                        sAccel:
                          AccelThresh_mm_ss: 30
                          AccelThresh_x10ms: 30
                          DecelThresh_mm_ss: 0
                          DecelThresh_x10ms: 300
                        sTime:
                          Accel_Coast_x10ms: 200
                          Coast_Brake_x10ms: 200
                          Brake_Spindown_x10ms: 100
            """

            # Set up the trackDB
            u8TrackIndex = sim.config.mission_profile.selected_profile
            sAccel = sim.config.mission_profile.profiles[u8TrackIndex].sAccel
            sTime = sim.config.mission_profile.profiles[u8TrackIndex].sTime

            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Accel__Threshold_mm_ss(u8TrackIndex,  sAccel.AccelThresh_mm_ss);
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Accel__Threshold_x10ms(u8TrackIndex, sAccel.AccelThresh_x10ms);
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Decel__Threshold_mm_ss(u8TrackIndex, sAccel.DecelThresh_mm_ss);
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Decel__Threshold_x10ms(u8TrackIndex, sAccel.DecelThresh_x10ms);
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Time__Accel_Coast_x10ms(u8TrackIndex, sTime.Accel_Coast_x10ms);
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Time__Coast_Brake_x10ms(u8TrackIndex, sTime.Coast_Brake_x10ms);
            sim.fcu.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Time__Brake_Spindown_x10ms(u8TrackIndex, sTime.Brake_Spindown_x10ms);


        elif self.state is "RUN_START":
            # Wait until the FCU says we're in READY state
            if sim.fcu.get_sm_state() == POD_STATE__READY:
                self.ready_state_counter += 1

            if self.ready_state_counter >= self.wait_steps_push:  # Wait some steps before pushing
                self.logger.info("Signaling pusher to start push")
                self.push_step_counter = 0  # Reset the push counter
                self.state = "START_PUSH"

        elif self.state is "START_PUSH":
            sim.pusher.start_push()
            self.pushed = True
            self.push_step_counter += 1
            self.state = "RUNNING"

        elif self.state is "RUNNING":
            if self.push_step_counter == 10:  # rough approx of accel detection
                # Pretend that we've detected acceleration
                # Note: This might get reset before it's checked to trigger the transition...
                # @todo: make this a bit better by using actual accel values?
                # Note: this will be replaced once accelerometers are working
                #sim.fcu.lib.u8FCU_ACCEL_THRESH__Debug_Set_Accel_Threshold_Met(1)

                if self.fake_accel_transition:
                    sim.fcu.lib.vFCU_FCTL_MAINSM__Debug__ForceState(POD_STATE__ACCEL);

            if sim.fcu.get_sm_state() is POD_STATE__BRAKE:
                # Apply the brakes
                sim.pod.brakes.apply()
            else:
                # Stop the brakes
                sim.pod.brakes.hold()

            if sim.pusher.state is not "COAST":
                self.push_step_counter += 1

            if sim.fcu.get_sm_state() is POD_STATE__SPINDOWN:
                self.state = "FINISHING"

        elif self.state is "FINISHING":
            self.sim_finished = True


            if sim.fcu.get_sm_state() is POD_STATE__SPINDOWN:
                if self.end_after_spindown:
                    self.sim_finished = True

            # If we've returned to IDLE after spindown
            elif sim.fcu.get_sm_state() is POD_STATE__IDLE:
                if self.end_after_spindown:
                    self.sim_finished = True
            else:
                # keep going
                pass

    # @todo: add this as the only sim end listener
    def is_finished(self, sim):
        if self.sim_finished:
            return True
        else:
            return False


class StateMachineInteractiveController(object):
    """ Control the FCU state and pusher for a simulated run """

    def __init__(self):
        self.logger = logging.getLogger("StateMachineInteractiveController")
        """
        self.started = False
        self.pushed = False
        """

    def setup_mission_profile(self):
        pass

    def step_callback(self, sim):
        pass
        """
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
        """

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

    #from debug import stacktracer
    #stacktracer.trace_start("trace.html",interval=5,auto=True) # Set auto flag to always update file!

    with open('conf/logging.conf') as f:  # @todo: make this work when run from anywhere (this works if run from top directory)
        logging.config.dictConfig(yaml.load(f))
        
    test_logger = logging.getLogger("NetworkNode")
    #print(test_logger.__dict__)


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

    # @todo: add command line arguments to specify which mode to run in (interactive/auto)

    # Testing run controller (with pod state machine control)

    # @todo: consider moving end listeners into a 'sim controller' concept
    run_controller = StateMachineRunController()
    sim.add_step_listener(run_controller)
    # sim.add_end_condition(run_controller)  # Temporarily disabled for testing / integration of network-based control

    # Testing interactive controller (can talk to it with the RPOD_CONTROL app)
    #sim.add_step_listener(StateMachineInteractiveController())

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