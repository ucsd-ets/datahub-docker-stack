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
import sys
from .gpu_tester_pb2 import *
from .gpu_tester_pb2_grpc import *

class _Kubectl:
    def __init__(self, subprocess=subprocess, os=os,job_template_path='/etc/gpu-tester/job-template.yaml', job_output_path='/var/lib/gpu-tester/job.yaml'):
        self.subprocess = subprocess
        self.job_template_path = job_template_path
        self.job_output_path = job_output_path

    def create_job(self, command=["kubectl","apply","-f"]) -> None:
        self.subprocess.run(command+[self.job_output_path])
    
    def get_logs_from_pod(self, command=["kubectl","logs","jobs/gpu-test-job"]) -> str:
        proc = self.subprocess.run(command, capture_output=True)
        job_out = proc.stdout
        return job_out
    
    def delete_job(self, command=["kubectl","delete","jobs/gpu-test-job"]) -> None:
        self.subprocess.run(command)


    def update_job_template(self, image : str, split_indicator="image: ") -> None:
        with open(self.job_template_path,'r')as file:
            job_temp = file.read()

        os.makedirs(os.path.dirname(self.job_output_path), exist_ok=True)
        with open(self.job_output_path,'w') as file:
            index = job_temp.index(split_indicator) + len(split_indicator)
            new_job = job_temp[:index:] + image + job_temp[index::]
            file.write(new_job)


class GrpcService:
    def reply(message, context):
        return GpuTesterReply(test_output=message)

class GpuTester(GpuTesterServicer):
    """
    Facade for integrating kubectl operations & grpc replies
    """
    def __init__(self, kubectl: _Kubectl, timeout=60, grpc_replier=GpuTesterReply, charset="utf-8"):
        self.kubectl = kubectl
        self.timeout_seconds: int = timeout
        self.grpc_replier = grpc_replier
        self.timeout_json = {'torch':False, 'tensorflow': False, 'msg':'Test Failed: Timeout reached.' }
        self.charset = charset

    def LaunchGpuJob(self, request, context):
        self.kubectl.update_job_template(request.image)
        self.kubectl.create_job()
        timeout = time.time() + self.timeout_seconds

        job_out = None
        while time.time() < timeout:
            try:
                job_out = self.kubectl.get_logs_from_pod().decode(self.charset)
            except Exception as ex:
                self.timeout_json['msg']=str(ex)
                pass
            if not (job_out is None or job_out == ""):
                self.kubectl.delete_job()
                return self.grpc_replier(test_output=job_out)
            time.sleep(1)

        self.kubectl.delete_job()
        out = json.dumps(self.timeout_json,indent=2)
        return self.grpc_replier(test_output=out)


class GpuTesterServer(GpuTesterServicer):
    def __init__(self, gpu_tester=GpuTester(_Kubectl())):
        self.gpu_tester = gpu_tester
    
    def LaunchGpuJob(self, request, context):
        return self.gpu_tester.LaunchGpuJob(request, context)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_GpuTesterServicer_to_server(GpuTester(_Kubectl()), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()