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
import json
from tracemalloc import start
import grpc
import time
from .gpu_tester_pb2 import *
from .gpu_tester_pb2_grpc import *

class Client():
    def __init__(self, test_image, url, cer_path, timeout):
        self.test_image = test_image
        self.url = url
        self.cer_path = cer_path
        self.timeout = timeout

    def ping_server(self, cmd) -> json:
        credentials = self._get_credentials()
        with grpc.secure_channel(self.url,credentials) as channel:
            stub = GpuTesterStub(channel)
            response = stub.LaunchGpuJob(GpuTesterRequest(image=self.test_image,command=cmd),timeout=self.timeout)
            return json.loads(response.test_output)

    def _get_credentials(self):
        if self.cer_path:
            with open(self.cer_path, 'rb') as f:
                return grpc.ssl_channel_credentials(f.read())
        else:
            return grpc.ssl_channel_credentials(os.environ['GRPC_CERT'].encode())

def run(test_image = 'ucsdets/scipy-ml-notebook:2021.3-stable', url = 'dsmlp.grpc-services.ucsd.edu:443', cer_path='dsmlp_grpc-services_ucsd_edu_interm.cer', timeout=1200) -> str:
    client = Client(test_image,url,cer_path,timeout)

    status = client.ping_server("start")
    while status['state'] == 'running':
        time.sleep(5)
        status = client.ping_server("status")
    print(json.dumps(status,indent=2))
    return f'Test result:\n{status["test_output"]}'




    


if __name__ == '__main__':
    logging.basicConfig()
    print(run())