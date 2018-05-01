#!/usr/bin/env python

from __future__ import print_function

import random
import time

import grpc

import simulator_control_pb2
import simulator_control_pb2_grpc

SIM_CTRL_RUN = 0
SIM_CTRL_PAUSE = 1
SIM_CTRL_STOP = 2

PUSHER_CTRL_PUSH = 3

def start(stub):
    result = stub.ControlSim(simulator_control_pb2.SimCommand(command=SIM_CTRL_RUN))
    print("Start result: {}".format(result))

def pause(stub):
    result = stub.ControlSim(simulator_control_pb2.SimCommand(command=SIM_CTRL_PAUSE))
    print("Pause result: {}".format(result))

def unpause(stub):
    result = stub.ControlSim(simulator_control_pb2.SimCommand(command=SIM_CTRL_RUN))
    print("Unpause result: {}".format(result))

def stop(stub):
    result = stub.ControlSim(simulator_control_pb2.SimCommand(command=SIM_CTRL_STOP))
    print("Stop result: {}".format(result))

def start_push(stub):
    result = stub.ControlSim(simulator_control_pb2.SimCommand(command=PUSHER_CTRL_PUSH))
    print("Start Push result: {}".format(result))

def run():
    print("Starting test client")
    channel = grpc.insecure_channel('localhost:9333')
    stub = simulator_control_pb2_grpc.SimControlStub(channel)
    print("-------------- Start --------------")
    start(stub)
    time.sleep(5)
    print("-------------- Start again (should error) --------------")
    start(stub)
    time.sleep(2)

    print("-------------- Start Push --------------")
    start_push(stub)
    time.sleep(5)
    print("-------------- Pause --------------")
    pause(stub)
    time.sleep(1)
    print("-------------- Unpause --------------")
    unpause(stub)
    time.sleep(3)
    print("-------------- Stop --------------")
    stop(stub)
    time.sleep(3)
    print("-------------- Start --------------")
    start(stub)
    time.sleep(5)
    print("-------------- Stop --------------")
    stop(stub)


if __name__ == '__main__':
    run()