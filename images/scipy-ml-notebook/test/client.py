# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Python implementation of the GRPC superqa.Greeter client."""

from __future__ import print_function

import logging
import os
import grpc
from gpu_tester_pb2 import *
from gpu_tester_pb2_grpc import *


def run(test_image = 'ucsdets/scipy-ml-notebook:2021.3-stable', url = 'dsmlp.grpc-services.ucsd.edu:443', cer_path='superqa_roots.cer', timeout_seconds=300) -> str:
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    if cer_path:
        with open(cer_path, 'rb') as f:
            credentials = grpc.ssl_channel_credentials(f.read())
    else:
        credentials = grpc.ssl_channel_credentials(os.environ['GRPC_CERT'].encode())
    with grpc.secure_channel(url,credentials) as channel:
        stub = GpuTesterStub(channel)
        response = stub.LaunchGpuJob(GpuTesterRequest(image=test_image),timeout=None)
        return f'Test response :\n{response.test_output}'


if __name__ == '__main__':
    logging.basicConfig()
    print(run())