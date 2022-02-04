import pytest
import subprocess
import os
import json
from unittest.mock import MagicMock
from gpu_tester.client import *

EXAMPLE_GOOD_OUT='Test response :\n{\n  "torch": true,\n  "tensorflow": true,\n  "msg": ""\n}\n'
EXAMPLE_MISSING_PACKAGE = "Test response :\nImage missing a necessary package: No module named 'tensorflow'\n"
EXAMPLE_TIME_OUT = 'Test response :\n{\n  "torch": false,\n  "tensorflow": false,\n  "msg": "Test Failed: Timeout reached."\n}'
path_to_cer = 'gpu_tester/superqa_roots.cer'

def test_gpu_tester():
    # positive case
    assert run(cer_path=path_to_cer) == EXAMPLE_GOOD_OUT
    # image doesn't exist
    assert run(test_image='invalid_image_for_test',cer_path=path_to_cer) == EXAMPLE_TIME_OUT
    # image lacks tools to perform test
    assert run(test_image='python',cer_path=path_to_cer) == EXAMPLE_MISSING_PACKAGE