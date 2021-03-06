# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import simulator_control_pb2 as simulator__control__pb2


class SimControlStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.ControlSim = channel.unary_unary(
        '/simproto.SimControl/ControlSim',
        request_serializer=simulator__control__pb2.SimCommand.SerializeToString,
        response_deserializer=simulator__control__pb2.Ack.FromString,
        )
    self.InitSim = channel.unary_unary(
        '/simproto.SimControl/InitSim',
        request_serializer=simulator__control__pb2.SimInit.SerializeToString,
        response_deserializer=simulator__control__pb2.Ack.FromString,
        )


class SimControlServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def ControlSim(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def InitSim(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_SimControlServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'ControlSim': grpc.unary_unary_rpc_method_handler(
          servicer.ControlSim,
          request_deserializer=simulator__control__pb2.SimCommand.FromString,
          response_serializer=simulator__control__pb2.Ack.SerializeToString,
      ),
      'InitSim': grpc.unary_unary_rpc_method_handler(
          servicer.InitSim,
          request_deserializer=simulator__control__pb2.SimInit.FromString,
          response_serializer=simulator__control__pb2.Ack.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'simproto.SimControl', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
