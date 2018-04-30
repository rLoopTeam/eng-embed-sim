#!/usr/bin/env python

from concurrent import futures
import time
import math

import grpc

import simulator_control_pb2
import simulator_control_pb2_grpc

from sim import Sim


_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class SimControlServicer(simulator_control_pb2_grpc.SimControlServicer):
    
    def __init__(self):
        self.sim = None

    def ControlSim(self, request, context):
        cmd = request.Command
        # @todo: check to make sure things worked properly before returning
        if cmd == 0:    # Start simulator
            msg = "Received StartSimulator"
            self.sim.run_threaded()  # @todo: run threaded? 
            # @todo: wait to return until we're sure the sim has started properly? 
        elif cmd == 1:  # Pause simulator
            msg = "Received PauseSimulator"
            self.sim.pause()
        elif cmd == 2:  # Resume simulator
            msg = "Received ResumeSimulator"
            self.sim.resume()
        elif cmd == 3:  # Stop simulator
            msg = "Received StopSimulator"
            self.sim.stop()
        else:
            msg = "Error -- command {} was not recognized".format(str(cmd))

        return simulator_control_pb2.Ack(success=True, message=msg)

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