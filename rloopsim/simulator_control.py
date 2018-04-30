#!/usr/bin/env python

from concurrent import futures
import time
import math

import grpc

import simulator_control_pb2
import simulator_control_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class SimControlServicer(simulator_control_pb2_grpc.SimControlServicer):
    
    def __init__(self):
        self.sim = None

    def ControlSim(self, request, context):
        cmd = request.Command
        if cmd == 0:    # Start simulator
            msg = "Received StartSimulator"  
        elif cmd == 1:  # Pause simulator
            msg = "Received PauseSimulator"
        elif cmd == 2:  # Resume simulator
            msg = "Received ResumeSimulator"
        elif cmd == 3:  # Stop simulator
            msg = "Received StopSimulator"
        else:
            msg = "Error -- command {} was not recognized".format(str(cmd))

        return simulator_control_pb2.Ack(success=True, message=msg)

        #context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        #context.set_details('Method not implemented!')
        #raise NotImplementedError('Method not implemented!')


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    simulator_control_pb2_grpc.add_SimControlServicer_to_server(
        SimControlServicer(), server)
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
    serve()