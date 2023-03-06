from dataclasses import dataclass, field
from typing import List, Dict
import os
import logging
import json
import pytest

from scripts.v2.tree import Node, build_tree, load_spec
from scripts.v2 import docker_adapter
from scripts.v2 import fs
from scripts.v2 import wiki


logger = logging.getLogger('datahub_docker_stacks')

class RunnerError(Exception):
    pass

@dataclass
class Result:
    success: bool = False
    message: str = ''
    full_image_name: str = ''
    container_details: Dict = field(default_factory=dict)
    test_results: Dict = field(default_factory=dict)

    def __bool__(self):
        return any([
            self.success,
            self.message,
            self.full_image_name,
            self.container_details,
            self.test_results,
        ])

    def append_message(self, msg: str):
        if not msg:
            self.message = msg
        else:
            self.message += f'; {msg}'


def format_result(result: Result):
    details = {
        'image_name': result.full_image_name,
        'success': result.success,
        'message': result.message,
        'container_details': result.container_details
    }
    return json.dumps(details, indent=4)




def get_basic_test_locations(node: Node, stackdir='images', test_common_dirname='tests_common') -> List[str]:
    if not node.filepath:
        raise RunnerError(f'Must specify node.filepath for {node}')
    common_tests = os.path.join(stackdir, test_common_dirname)
    return [common_tests, node.filepath]


def run_tests(testdirs: List[str], pytest_exec=pytest.main) -> pytest.ExitCode:
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
        format_result=format_result,
        store_result=fs.store,
        test_runner=run_tests):
    
    login(username, password)

    # search the nodes according to BFS and place into node_order for processing
    

    # load all_info_cmds from spec.yml and pass to wiki operations
    all_info_cmds = load_spec()['all_info_cmds']

    # Run BFS or whatever search method
    # goal: make sure that the code can continue if a leaf node fails
    q = [root]
    node_order = []
    while q:
        # search the nodes according to BFS and place into node_order for processing
        for _ in range(len(q)):
            node = q.pop(0)
            node.image_tag = tag_prefix + '-' + node.git_suffix
            node_order.append(node)

            for child in node.children:
                if node.rebuild:
                    child.rebuild = True
                # set the tag for the child
                child.build_args.update({
                    "BASE_TAG": node.image_tag
                })
                q.append(child)

    results = []
    for node in node_order:
        logger.info(f'Processing node = {node.image_name}')

        result = Result(full_image_name=node.image_name +
                            ':' + node.image_tag)
        if not node.rebuild:
            logger.info(f"skipping node {node.image_name}")
            result.container_details['image_built'] = False
            result.success = True
            results.append(result)
            continue
    

        
        # build image
        image_built, report = build(node)
        result.container_details['build_log'] = report
        if not image_built:
            result.success = False
            results.append(result)
            continue
        
        # basic and common tests
        os.environ['TEST_IMAGE'] = node.image_name + ':' + node.image_tag
        testdirs = get_basic_test_locations(node)
        exit_code = test_runner(testdirs)
        result.test_results['basic_tests'] = 'Passed basic tests'
        if exit_code != pytest.ExitCode.OK:
            result.success = False
            result.test_results['basic_tests'] = 'Failed basic tests'
            results.append(result)
            continue
        
        # push step
        resp, report = push(node)
        result.container_details['push_success'] = resp
        result.container_details['push_log'] = report
        
        if not resp:
            results.success = False
            results.append(result)
            continue
    
        # integration tests
        if node.integration_tests:
            exit_code = test_runner(os.path.join(node.filepath, 'integration'))

            result.test_results['integration_tests'] ='Passed integration tests'
            if exit_code != pytest.ExitCode.OK:
                result.success = False
                result.test_results['integration_tests'] ='Failed integration tests'
                results.append(result)
                continue

        # update wiki page of individual image
        wiki.write_report(node, all_info_cmds)


        results.append(result)


    # store results
    for result in results:
        formatted_result = format_result(result)
        resp = store_result(os.path.join(fs.ARTIFACTS_PATH, result.full_image_name), formatted_result)
        if not resp:
            raise OSError("couldn't store results into artifacts directory")
    


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
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
