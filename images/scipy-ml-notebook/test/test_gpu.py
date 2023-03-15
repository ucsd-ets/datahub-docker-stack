import pytest
import os
from grpc_files.gpu_tester.client import *

EXAMPLE_GOOD_OUT='Test result:\n{\n  "torch": true,\n  "tensorflow": true,\n  "msg": ""\n}\n'
EXAMPLE_MISSING_PACKAGE = "Test result:\nImage missing a necessary package: No module named 'tensorflow'\n"
EXAMPLE_TIME_OUT = '{\n  "torch": false,\n  "tensorflow": false,\n  "msg": "Test Failed: Timeout reached."\n}'


@pytest.fixture(scope='function')
def untested_image():
    image = os.environ['TEST_IMAGE']
    repo,tag = image.split(":")
    tag = tag+'-untested'
    return f'{repo}:{tag}'

# @pytest.mark.skip(reason="Skipping test_gpu_valid() due to grpc issue")
def test_gpu_valid(untested_image):
    assert run(create_client(test_image=untested_image,cer_path=None, timeout=600)) == EXAMPLE_GOOD_OUT, \
        f"Image name: {untested_image}, gpu is not available for torch or tensorflow" 

# @pytest.mark.skip(reason="Skipping test_gpu_nonexistent_image() due to grpc issue")
def test_gpu_nonexistent_image():
    response = json.loads(run(create_client(test_image='invalid_image_for_test',cer_path=None, timeout=200)))
    assert response['test_output'] == EXAMPLE_TIME_OUT

@pytest.mark.skip(reason="Skipping test_gpu_lacking_tools() to debug; not necessary")
def test_gpu_lacking_tools():
    assert run(create_client(test_image='python',cer_path=None)) == EXAMPLE_MISSING_PACKAGE
