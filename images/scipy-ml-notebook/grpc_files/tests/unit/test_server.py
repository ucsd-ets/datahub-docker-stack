import pytest
import subprocess
import os
import json
from unittest.mock import MagicMock
from gpu_tester.server import *

JOB_TEMPLATE_PATH='/tmp/gpu-tester/etc'
JOB_OUTPUT_PATH='/tmp/gpu-tester/var/lib'
EXAMPLE_POSITIVE_RESPONSE = "{'torch':True, 'tensorflow': True, 'msg':'' }"

@pytest.fixture
def setup_test_dirs():
    subprocess.run(['mkdir', '-p', JOB_TEMPLATE_PATH, JOB_OUTPUT_PATH])
    subprocess.run(['cp', '/etc/gpu-tester/job-template.yaml', '/tmp/gpu-tester/etc'])

    yield
    subprocess.run(['rm', '-rf', '/tmp/gpu-tester'])

@pytest.fixture
def mock_kubectl(setup_test_dirs):
    kubectl = MagicMock()
    kubectl.create_job = MagicMock()
    kubectl.get_logs_from_pod = MagicMock(return_value=EXAMPLE_POSITIVE_RESPONSE)
    kubectl.delete_job = MagicMock()
    kubectl.update_job_template = MagicMock()
    kubectl.get_events = MagicMock(return_value = b"logs")
    return kubectl

def test_gpu_tester(mock_kubectl):
    # positive case scenario
    gputester = GpuTester(
        mock_kubectl, 
        grpc_replier=MagicMock(return_value=EXAMPLE_POSITIVE_RESPONSE)
    )  

    fake_img = 'myfakeimage:tag'
    mock_context = MagicMock()
    mock_context.time_remaining  = MagicMock(return_value=1)
    mock_request = MagicMock()
    mock_request.image = fake_img

    # actual method under test
    result = gputester.LaunchGpuJob(mock_request,mock_context)
    assert result == EXAMPLE_POSITIVE_RESPONSE

    mock_kubectl.update_job_template.assert_called_with(fake_img)
    mock_kubectl.create_job.assert_called()
    gputester.grpc_replier.assert_called()

    # test that timeout occurs with false reply
    def raise_exception():
        raise Exception('')
    mock_kubectl.get_logs_from_pod = raise_exception
    
    gputester = GpuTester(
        mock_kubectl, 
        grpc_replier=MagicMock(return_value=EXAMPLE_POSITIVE_RESPONSE)
    )
    mock_context.time_remaining  = MagicMock(return_value=0)
    gputester.LaunchGpuJob(mock_request,mock_context)
    mock_kubectl.delete_job.assert_called()
    assert gputester._timeout_occured()
    
