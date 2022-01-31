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
import gpu_tester_pb2
import gpu_tester_pb2_grpc


class GpuTester(gpu_tester_pb2_grpc.GpuTesterServicer):

    def LaunchGpuJob(self, request, context):
        self._update_job(request.image)
        subprocess.run(["kubectl","apply","-f","job.yaml"])
        timeout = time.time() + 60
        
        while time.time() < timeout:
            try:
                proc = subprocess.run(["kubectl","logs","jobs/gpu-test-job"],capture_output=True)
                job_out = proc.stdout
            except Exception as ex:
                pass

            if len(job_out):
                subprocess.run(["kubectl","delete","job","gpu-test-job"])
                print(job_out)
                return gpu_tester_pb2.GpuTesterReply(test_output=job_out)
            time.sleep(1)
        
        subprocess.run(["kubectl","delete","job","gpu-test-job"])
        timeout_json = {'torch':False, 'tensorflow': False, 'cuda': False, 'msg':'Test Failed: Timeout reached.' }
        print('timeout')
        return gpu_tester_pb2.GpuTesterReply(test_output=json.dumps(timeout_json,indent=2))
        
    def _update_job(self, image):
        with open('job-template.yaml','r')as file:
            old_job = file.read()
        new_job=old_job
        # insert image in the yaml file without editing anything else
        new_job = f'{old_job[:old_job.index("image: ")+7:]}{image}{old_job[old_job.index("image: ")+7::]}'
        with open('job.yaml','w') as file:
            file.write(new_job)
    


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gpu_tester_pb2_grpc.add_GpuTesterServicer_to_server(GpuTester(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()