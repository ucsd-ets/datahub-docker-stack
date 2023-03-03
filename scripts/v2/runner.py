from scripts.v2.tree import Node, build_tree
from scripts.v2 import docker_adapter
from dataclasses import dataclass
from typing import List
import os
import logging
import pytest

logger = logging.getLogger('datahub_docker_stacks')


@dataclass
class Result:
    success: bool = False
    message: str = ''
    full_image_name: str = ''
    container_buildlog: str = ''

    def append_message(self, msg: str):
        if not msg:
            self.message = msg
        else:
            self.message += f'; {msg}'


class RunnerError(Exception):
    pass


def get_basic_test_locations(node: Node, stackdir='images', test_common_dirname='tests_common') -> List[str]:
    if not node.filepath:
        raise RunnerError(f'Must specify node.filepath for {node}')
    common_tests = os.path.join(stackdir, test_common_dirname)
    return [common_tests, node.filepath]


def run_tests(node: Node, testdirs: List[str], pytest_exec=pytest.main) -> pytest.ExitCode:
    exit_code = pytest_exec([
        '-x',
        *testdirs
    ])

    return exit_code


def run_basic_tests(node: Node, testdirs: List[str], pytest_exec=pytest.main) -> pytest.ExitCode:
    # find test dirs
    os.environ['TEST_IMAGE'] = node.image_name + ':' + node.image_tag
    exit_code = pytest_exec([
        '-x',
        *testdirs
    ])

    return exit_code


def run_integration_tests(node: Node, result: Result, pytest_exec=pytest.main) -> bool:
    integration_testpath = os.path.join(node.filepath, 'test', 'integration')
    if not os.path.exists(integration_testpath):
        result.success = False
        result.append_message('no integration test path')
        return False


def build_and_test_containers(
        root: Node,
        username: str,
        password: str,
        tag_prefix: str,
        build=docker_adapter.build,
        push=docker_adapter.push,
        login=docker_adapter.login,
        test_runner=run_tests):
    # Run BFS or whatever search method
    # goal: make sure that the code can continue if a leaf node fails
    login(username, password)

    results = []
    q = [root]
    while q:
        for _ in range(len(q)):
            node = q.pop(0)
            node.image_tag = tag_prefix + '-' + node.git_suffix
            logger.info(f'Processing node = {node.image_name}')
            result = Result(full_image_name=node.image_name +
                            ':' + node.image_tag)

            skip_build = False
            if not node.rebuild:
                skip_build = True

            image_built = False
            if not skip_build:
                image_built, report = build(node)
                result.container_buildlog = report

                if not image_built:
                    result.success = False
                    result.append_message("image building failed, see build log")
                    results.append(result)
                
                else:
                    os.environ['TEST_IMAGE'] = node.image_name + ':' + node.image_tag
                    testdirs = get_basic_test_locations(node)
                    exit_code = test_runner(node, testdirs)

                    if exit_code != pytest.ExitCode.OK:
                        result.success = False
                        result.append_message("failed basic tests")
            
            if not skip_build and image_built:
                # push
                push(node)
            
            if not skip_build and image_built and node.integration_tests:
                # run the integration tests
                exit_code = test_runner(node, os.path.join(node.filepath, 'integration'))
                if exit_code != pytest.ExitCode.OK:
                    result.success = False
                    result.append_message('Failed integration tests')

            # update wiki

            for child in node.children:
                if node.rebuild:
                    child.rebuild = True
                # set the tag for the child
                child.build_args.update({
                    "BASE_TAG": node.image_tag
                })
                q.append(child)


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    test_spec = {
        'images': {
                'datahub-base-notebook': {
                    'build_args': {
                        'PYTHON_VERSION': 'python-3.9.5'
                    }
                },
                'datascience-notebook': {
                    'depend_on': 'datahub-base-notebook'
                }
        }
    }

    tree = build_tree(test_spec, ['datahub-base-notebook'], 'test')
    
    dockerhub_username = os.environ.get('DOCKERHUB_USERNAME', None)
    dockerhub_token = os.environ.get('DOCKERHUB_TOKEN', None)
    if not dockerhub_username or not dockerhub_token:
        logging.error('dockerhub username or password not set')
        exit(1)
    
    build_and_test_containers(tree, dockerhub_username, dockerhub_token, 'test')
