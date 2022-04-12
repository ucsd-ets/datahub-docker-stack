# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from .gpu_tester_pb2 import *


class GpuTesterStub(object):
    """The test service definition.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.LaunchGpuJob = channel.unary_unary(
                '/gpu_tester.GpuTester/LaunchGpuJob',
                request_serializer=GpuTesterRequest.SerializeToString,
                response_deserializer=GpuTesterReply.FromString,
                )


class GpuTesterServicer(object):
    """The test service definition.
    """

    def LaunchGpuJob(self, request, context):
        """Sends container_name:tag for testing
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_GpuTesterServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'LaunchGpuJob': grpc.unary_unary_rpc_method_handler(
                    servicer.LaunchGpuJob,
                    request_deserializer=GpuTesterRequest.FromString,
                    response_serializer=GpuTesterReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'gpu_tester.GpuTester', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class GpuTester(object):
    """The test service definition.
    """

    @staticmethod
    def LaunchGpuJob(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/gpu_tester.GpuTester/LaunchGpuJob',
            GpuTesterRequest.SerializeToString,
            GpuTesterReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
