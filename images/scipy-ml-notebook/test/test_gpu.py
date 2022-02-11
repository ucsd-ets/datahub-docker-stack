import os
from grpc_files.gpu_tester.client import *

EXAMPLE_GOOD_OUT='Test response :\n{\n  "torch": true,\n  "tensorflow": true,\n  "msg": ""\n}\n'
EXAMPLE_MISSING_PACKAGE = "Test response :\nImage missing a necessary package: No module named 'tensorflow'\n"
EXAMPLE_TIME_OUT = 'Test response :\n{\n  "torch": false,\n  "tensorflow": false,\n  "msg": "Test Failed: Timeout reached."\n}'

def test_gpu_valid():
    assert run(test_image=os.environ['TEST_IMAGE'],cer_path=None) == EXAMPLE_GOOD_OUT
    
def test_gpu_nonexistent_image():
    assert run(test_image='invalid_image_for_test',cer_path=None) == EXAMPLE_TIME_OUT
    
def test_gpu_lacking_tools():
    assert run(test_image='python',cer_path=None) == EXAMPLE_MISSING_PACKAGE
