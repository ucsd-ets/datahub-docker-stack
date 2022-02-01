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
"""The Python implementation of the GRPC superqa.Greeter server."""

from concurrent import futures
import logging
import json
import subprocess
import time 
import os
import grpc
from .gpu_tester_pb2 import *
from .gpu_tester_pb2_grpc import *

class _Kubectl:
    def __init__(self, subprocess=subprocess):
        self.subprocess = subprocess

    def create_job(self) -> None:
        self.subprocess.run(["kubectl","apply","-f", self.job_output_path])
    
    def get_logs_from_pod(self) -> str:
        proc = self.subprocess.run(["kubectl","logs","jobs/gpu-test-job"],capture_output=True)
        job_out = proc.stdout
        return job_out
    
    def delete_job(self) -> None:
        self.subprocess.run(["kubectl","delete","job","gpu-test-job"])


    def update_job_template(self, image):
        with open(self.job_template_path,'r')as file:
            old_job = file.read()
        new_job=old_job
        # insert image in the yaml file without editing anything else
        new_job = f'{old_job[:old_job.index("image: ")+7:]}{image}{old_job[old_job.index("image: ")+7::]}'
        with open(self.job_output_path, 'w') as file:
            file.write(new_job)


class GrpcService(GpuTesterServicer):
    pass

class GpuTester:
    """
    Facade for integrating kubectl operations & grpc replies
    """
    def __init__(self, kubectl: _Kubectl, timeout=60, job_template_path='/etc/gpu-tester/job-template.yaml', job_output_path='/var/lib/gpu-tester/job.yaml', grpc_service=GrpcService):
        self.kubectl = kubectl
        self.timeout_seconds: int = timeout
        self.job_template_path = job_template_path
        self.job_output_path = job_output_path
        self.grpc_service = grpc_service
        self.timeout_json = "{'torch':False, 'tensorflow': False, 'cuda': False, 'msg':'Test Failed: Timeout reached.' }"

    def LaunchGpuJob(self, request):
        self.kubectl.update_job_template(request.image)
        self.kubectl.create_job()
        timeout = time.time() + self.timeout_seconds

        job_out = None
        while time.time() < timeout:
            try:
                job_out = self.kubectl.get_logs_from_pod()
            except Exception as ex:
                pass

            if job_out is not None:
                self.kubectl.delete_job()
                print(job_out)
                return self.grpc_service.GpuTesterReply(test_output=job_out)
            time.sleep(1)

        self.kubectl.delete_job()
        print('timeout')
        return self.grpc_service.GpuTesterReply(test_output=self.timeout_json)


class GpuTesterServer:
    def __init__(self, gpu_tester=GpuTester):
        self.gpu_tester = GpuTester()
    
    def LaunchGpuJob(self, request, context):
        return self.gpu_tester(request)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gpu_tester_pb2_grpc.add_GpuTesterServicer_to_server(GpuTesterServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()