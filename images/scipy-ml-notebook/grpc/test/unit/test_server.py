import pytest
import subprocess
import os
import json
from unittest.mock import MagicMock
from gpu_tester.server import *

JOB_TEMPLATE_PATH='/tmp/gpu-tester/etc'
JOB_OUTPUT_PATH='/tmp/gpu-tester/var/lib'
EXAMPLE_POSITIVE_RESPONSE = "{'torch':True, 'tensorflow': True, 'cuda': False, 'msg':'Test Failed: Timeout reached.' }"

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
    return kubectl


@pytest.fixture
def mock_grpc_service():
    grpc_server = MagicMock()
    grpc_server.GpuTesterReply = MagicMock(return_value=EXAMPLE_POSITIVE_RESPONSE)
    return grpc_server

def test_gpu_tester(mock_kubectl, mock_grpc_service):
    # positive case scenario
    gputester = GpuTester(
        mock_kubectl, 
        timeout=1, 
        job_template_path=JOB_TEMPLATE_PATH + '/job-template.yaml', 
        job_output_path=JOB_OUTPUT_PATH + '/job.yaml',
        grpc_service=mock_grpc_service
    )  

    fake_img = 'myfakeimage:tag'
    mock_request = MagicMock()
    mock_request.image = fake_img

    # actual method under test
    result = gputester.LaunchGpuJob(mock_request)
    assert result == EXAMPLE_POSITIVE_RESPONSE

    mock_kubectl.update_job_template.assert_called_with(fake_img)
    mock_kubectl.create_job.assert_called()
    mock_grpc_service.GpuTesterReply.assert_called()

    # test that timeout occurs with false reply
    def raise_exception():
        raise Exception('')
    mock_kubectl.get_logs_from_pod = raise_exception
    
    gputester = GpuTester(
        mock_kubectl, 
        timeout=1, 
        job_template_path=JOB_TEMPLATE_PATH + '/job-template.yaml', 
        job_output_path=JOB_OUTPUT_PATH + '/job.yaml',
        grpc_service=mock_grpc_service
    )

    gputester.LaunchGpuJob(mock_request)
    mock_kubectl.delete_job.assert_called()

    mock_grpc_service.GpuTesterReply.assert_called_with(gputester.timeout_json)
    


# def test_gpu_tester(mock_kubectl, setup_test_dirs):
#     gpu_tester = GpuTester(mock_kubectl)