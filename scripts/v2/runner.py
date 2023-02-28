from scripts.v2.tree import Node
from scripts.v2 import docker
from scripts.v2 import runner
from dataclasses import dataclass
from typing import List
import os
import pytest


@dataclass
class Result:
    success: bool = False
    message: str = ''
    full_image_name: str = ''

class RunnerError(Exception):
    pass


def get_basic_test_locations(node: Node, stackdir='images', test_common_dirname='tests_common') -> List[str]:
    if not node.filepath:
        raise RunnerError(f'Must specify node.filepath for {node}')
    common_tests = os.path.join(stackdir, test_common_dirname)
    return [common_tests, node.filepath]

def run_basic_tests(node: Node, testdirs: List[str], pytest_exec = pytest.main) -> pytest.ExitCode:
    # find test dirs
    os.environ['TEST_IMAGE'] = node.image_name + ':' + node.image_tag
    exit_code = pytest_exec([
        '-x',
        *testdirs
    ])

    return exit_code


def build_and_test_tree(root: Node, username: str, password: str, build = docker.build, push = docker.push, login = docker.login):
    # Run BFS or whatever search method
    # goal: make sure that the code can continue if a leaf node fails

    login(username, password)

    results = []
    q = [root]
    while q:
        for _ in range(len(q)):
            node = q.pop(0)
            result = Result(full_image_name=node.image_name + ':' + node.image_tag)
            # if marked for rebuild
            
            if not node.rebuild:
                result.success = True
                result.message = 'not flagged for build'
                results.append(result)
                continue
            
            #   build
            image_built = build(node)

            if not image_built:
                result.success = False
                result.message = "image building failed, see error log"
                results.append(result)
                continue
    
            #   test
            testdirs = runner.get_basic_test_locations(node)
            exit_code = runner.run_basic_tests(node, testdirs)

            if exit_code != pytest.exit.OK:
                result.success = False
                result.message = 'failed basic tests'
                continue
    
            #   push
            push(node)

            #   integration tests


            #   update wiki
        
    pass