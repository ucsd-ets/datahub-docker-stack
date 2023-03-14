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
    def __init__(self, test_image, url, cer_path, timeout, grpc=grpc):
        self.test_image = test_image
        self.url = url
        self.cer_path = cer_path
        self.timeout = timeout
        self.grpc=grpc

    def ping_server(self, cmd) -> json:
        credentials = self._get_credentials()
        with self.grpc.secure_channel(self.url,credentials) as channel:
            stub = GpuTesterStub(channel)
            response = stub.LaunchGpuJob(GpuTesterRequest(image=self.test_image,command=cmd),timeout=self.timeout)
            return json.loads(response.test_output)

    def _get_credentials(self):
        if self.cer_path:
            with open(self.cer_path, 'rb') as f:
                return self.grpc.ssl_channel_credentials(f.read())
        else:
            return self.grpc.ssl_channel_credentials(os.environ['GRPC_CERT'].encode())

def create_client(test_image = 'ucsdets/scipy-ml-notebook:2023.1-stable', url = 'dsmlp.grpc-services.ucsd.edu:443', cer_path='dsmlp_grpc-services_ucsd_edu_interm.cer', timeout=1200) -> Client:
    return Client(test_image,url,cer_path,timeout)

def run(client: Client) -> str:
    print(f'Testing {client.test_image}')
    status = client.ping_server("start")
    while status['state'] == 'running':
        time.sleep(5)
        status = client.ping_server("status")
    status_json = json.dumps(status,indent=2)
    if status['state'] != 'passed':
        return status_json
    return f'Test result:\n{status["test_output"]}'




    


if __name__ == '__main__':
    logging.basicConfig()
    print(run(create_client()))