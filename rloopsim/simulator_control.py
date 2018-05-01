#!/usr/bin/env python

from concurrent import futures
import time
import math

import grpc

import simulator_control_pb2
import simulator_control_pb2_grpc

from sim import Sim


_ONE_DAY_IN_SECONDS = 60 * 60 * 24

SIM_CTRL_RUN = 0
SIM_CTRL_PAUSE = 1
SIM_CTRL_STOP = 2

PUSHER_CTRL_PUSH = 0

class SimControlServicer(simulator_control_pb2_grpc.SimControlServicer):
    
    def __init__(self):
        self.sim = None
        self.sim_initialized = False
        self.sim_state = SIM_CTRL_STOP

        # Keep track of these so we can re-initialize the sim after a run
        self.sim_config = None
        self.output_dir = None

    def _init_sim(self):
        self.sim = Sim(self.sim_config, self.output_dir)
        # Wait until the sim is ready (@todo: do we need this? Doesn't the constructor block until it's done?)
        while not self.sim.is_ready:
            time.sleep(0.1)
        self.sim_initialized = True

    def _reset_sim(self):
        self.sim.stop()
        # Wait until we're sure it's done
        while not self.sim.is_ended:
            time.sleep(0.1)
        self._init_sim()


    def ControlSim(self, request, context):
        cmd = request.command

        msg = None
        success = False

        if self.sim_state is SIM_CTRL_STOP:
            # Can transition to start (run)

            # 
            # @todo: *** need to reset the simulator when it is stopped. 

            if cmd == SIM_CTRL_RUN:
                self.sim.run_threaded()
                # @todo: wait/check for proper startup
                msg = "Simulation started"
                self.sim_state = SIM_CTRL_RUN
                success = True
            else:
                success = False
                msg = "Command not allowed in while simulator is stopped"

        elif self.sim_state is SIM_CTRL_RUN:
            # Can transition to pause or stop
            if cmd == SIM_CTRL_PAUSE:
                self.sim.pause()
                # @todo: wait/check for pause
                msg = "Simulation paused"
                success = True
                self.sim_state = SIM_CTRL_PAUSE
            elif cmd == SIM_CTRL_STOP:
                # Stop and reset the sim
                self._reset_sim()
                msg = "Simulation stopped"
                success = True
                self.sim_state = SIM_CTRL_STOP
            else:
                success = False
                msg = "Command not allowed in while simulator is running"

        elif self.sim_state is SIM_CTRL_PAUSE:
            # Can transition to run or stop
            if cmd == SIM_CTRL_RUN:
                self.sim.resume()
                # @todo: wait/check for resume
                msg = "Simulation (not) resumed"
                success = True
                self.sim_state = SIM_CTRL_RUN
            elif cmd == SIM_CTRL_STOP:
                self._reset_sim()
                # @todo: wait/check for stop
                msg = "Simulation stopped"
                success = True
                self.sim_state = SIM_CTRL_STOP
            else:
                success = False
                msg = "Command not allowed in while simulator is paused"

        else:
            raise RuntimeError("Somehow we've reached an impossible state.")

        return simulator_control_pb2.Ack(success=success, message=msg)

        #context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        #context.set_details('Method not implemented!')
        #raise NotImplementedError('Method not implemented!')


    def InitSim(self, request, context):
        """ Initialize a new Simulator, possibly with different config/settings """
        # NOTE: UNTESTED
        # @todo: Testing and error handling (e.g. config files won't load)

        # Initialize the simulator with the provided config files and output dir (or defaults)
        # Note: this should only work when the simulator is stopped
        if self.sim_state is not SIM_CTRL_STOP:
            msg = "Simulator must be stopped before initializing"
            return simulator_control_pb2.Ack(success=False, message=msg)


        config_files = ['conf/sim_config.yaml']
        # @todo: change this to something better, maybe a tmp file?
        output_dir = "../eng-embed-sim-data/test"
        if len(request.config_files):
            config_files = request.config_files

        if request.output_dir is not "":
            output_dir = request.output_dir
            
        # Load the configuration files 
        # @todo: error checking for config loading and output directory viability
        self.sim_config = Sim.load_config_files(config_files)
        self.output_dir = output_dir
        self._init_sim()

    def ControlPusher(self, request, context):
        """ Control the pusher """
        if request.command == PUSHER_CTRL_PUSH:
            self.sim.pusher.start_push()
            # @todo: wait/ensure success
            msg = "Push started"
            return simulator_control_pb2.Ack(success=False, message=msg)
        else:
            raise RuntimeError("Unrecognized pusher command '{}' received".format(request.command))


def serve(sim_config, working_dir):

    # Note: 'configfile' is a list of one or more config files. Later files overlay previous ones. 
    #sim = Sim(sim_config, '../eng-embed-sim-data/test')

    servicer = SimControlServicer()
    servicer.sim_config = sim_config
    servicer.output_dir = working_dir
    servicer._init_sim()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    simulator_control_pb2_grpc.add_SimControlServicer_to_server(
        servicer, server)
    grpc_port = 9333

    server.add_insecure_port("[::]:{}".format(grpc_port))
    print "Starting simulator control GRPC server on port {}".format(grpc_port)

    server.start()

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':

    # @todo: rework this to maybe have the initially specified config file optional (i.e. require initialization via servicer)

    # Temporary imputs -- copied from sim.py
    import sys
    import logging
    import logging.config
    import yaml
    from config import *
    import pprint
    import argparse

    #from debug import stacktracer
    #stacktracer.trace_start("trace.html",interval=5,auto=True) # Set auto flag to always update file!

    with open('conf/logging.conf') as f:  # @todo: make this work when run from anywhere (this works if run from top directory)
        logging.config.dictConfig(yaml.load(f))
        
    test_logger = logging.getLogger("NetworkNode")
    #print(test_logger.__dict__)

    parser = argparse.ArgumentParser(description="rPod Simulation")
    parser.add_argument('configfile', metavar='config', type=str, nargs='+', default="None",
        help='Simulation configuration file(s) -- later files overlay on previous files')
    args = parser.parse_args()

    sim_config = Sim.load_config_files(args.configfile)
    output_dir = "../eng-embed-sim-data/test"  # @todo: get this from command line args or something

    serve(sim_config, output_dir)