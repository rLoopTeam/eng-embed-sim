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

class SimControlServicer(simulator_control_pb2_grpc.SimControlServicer):
    
    def __init__(self):
        self.sim = None
        self.sim_state = SIM_CTRL_STOP

    def ControlSim(self, request, context):
        cmd = request.command

        msg = None
        success = False

        if self.sim_state is SIM_CTRL_STOP:
            # Can transition to start (run)
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
                self.sim.stop()
                # @todo: wait/check for stop
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
                msg = "Simulation resumed"
                success = True
                self.sim_state = SIM_CTRL_RUN
            elif cmd == SIM_CTRL_STOP:
                self.sim.stop()
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


def serve(config):


    # Note: 'configfile' is a list of one or more config files. Later files overlay previous ones. 
    sim = Sim(config, '../eng-embed-sim-data/test')

    servicer = SimControlServicer()
    servicer.sim = sim

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

    config = Sim.load_config_files(args.configfile)

    serve(config)