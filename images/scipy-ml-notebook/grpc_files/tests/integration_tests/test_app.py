import pytest
import subprocess
import os
import json
from unittest.mock import MagicMock
from gpu_tester.client import *

EXAMPLE_GOOD_OUT='Test result:\n{\n  "torch": true,\n  "tensorflow": true,\n  "msg": ""\n}\n'
EXAMPLE_MISSING_PACKAGE = "Test result:\nImage missing a necessary package: No module named 'tensorflow'\n"
EXAMPLE_TIME_OUT = '{\n  "torch": false,\n  "tensorflow": false,\n  "msg": "Test Failed: Timeout reached."\n}'
path_to_cer = 'gpu_tester/dsmlp_grpc-services_ucsd_edu_interm.cer'

def test_gpu_valid():
    assert run(create_client(cer_path=path_to_cer,timeout=60)) == EXAMPLE_GOOD_OUT
    
def test_gpu_nonexistent_image():
    response = json.loads(run(create_client(test_image='invalid_image_for_test',cer_path=path_to_cer,timeout=20)))
    assert  response['test_output']== EXAMPLE_TIME_OUT
    
def test_gpu_lacking_tools():
    assert run(create_client(test_image='python',cer_path=path_to_cer,timeout=60)) == EXAMPLE_MISSING_PACKAGE

def test_env_cert_valid():
    with open(path_to_cer, 'rb') as f:
        os.environ['GRPC_CERT']=f.read().decode()
    assert run(create_client(cer_path=None,timeout=60)) == EXAMPLE_GOOD_OUT
    
    