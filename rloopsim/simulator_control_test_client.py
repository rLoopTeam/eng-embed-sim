#!/usr/bin/env python

from __future__ import print_function

import random

import grpc

import simulator_control_pb2
import simulator_control_pb2_grpc


def start(stub):
    result = stub.ControlSim(simulator_control_pb2.SimCommand(Command=0))
    print("Start result: {}".format(result))

def pause(stub):
    result = stub.ControlSim(simulator_control_pb2.SimCommand(Command=1))
    print("Pause result: {}".format(result))

def unpause(stub):
    result = stub.ControlSim(simulator_control_pb2.SimCommand(Command=2))
    print("Unpause result: {}".format(result))

def stop(stub):
    result = stub.ControlSim(simulator_control_pb2.SimCommand(Command=3))
    print("Stop result: {}".format(result))

def run():
    print("Starting test client")
    channel = grpc.insecure_channel('localhost:9333')
    stub = simulator_control_pb2_grpc.SimControlStub(channel)
    print("-------------- Start --------------")
    start(stub)
    print("-------------- Pause --------------")
    pause(stub)
    print("-------------- Unpause --------------")
    unpause(stub)
    print("-------------- Stop --------------")
    stop(stub)


if __name__ == '__main__':
    run()