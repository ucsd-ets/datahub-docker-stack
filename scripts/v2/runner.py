from scripts.v2.utils import get_logger
from dataclasses import dataclass, field
from typing import List, Dict
import os
import yaml
import pytest
import logging


from scripts.v2.tree import Node, build_tree, load_spec
from scripts.v2 import docker_adapter
from scripts.v2 import fs
from scripts.v2 import wiki

logger = get_logger()

class RunnerError(Exception):
    pass


@dataclass
class Result:
    success: bool = False
    message: str = ''
    full_image_name: str = ''
    container_details: Dict = field(default_factory=dict)
    test_results: Dict = field(default_factory=dict)

    @property
    def safe_full_image_name(self):
        full_image_name = self.full_image_name
        safe_full_image_name = full_image_name.replace('/', '-')
        safe_full_image_name = safe_full_image_name.replace(':', '-')
        return safe_full_image_name

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
    return yaml.dump(result, indent=2)

class RunTestError(Exception):
    pass

def run_tests(testdirs: List[str], pytest_exec=pytest.main) -> pytest.ExitCode:
    exit_code = pytest_exec([
        '-x',
        *testdirs
    ])

    return exit_code

def get_basic_test_locations(node: Node, stackdir='images', test_common_dirname='tests_common') -> List[str]:
    if not node.filepath:
        raise RunTestError(f'Must specify node.filepath for {node}')
    common_tests = os.path.join(stackdir, test_common_dirname)
    return [common_tests, node.filepath]

def setup_testing_environment(node: Node):
    os.environ['TEST_IMAGE'] = node.image_name + ':' + node.image_tag

def run_basic_tests(node: Node, result: Result) -> bool:
    if not os.environ.get('TEST_IMAGE', None):
        raise RunTestError('You must specify TEST_IMAGE envar before running tests')
    test_locations = get_basic_test_locations(node)
    exit_code = run_tests(test_locations)

    result.test_results['basic_tests'] = 'Passed basic tests'
    if exit_code != pytest.ExitCode.OK:
        result.success = False
        result.test_results['basic_tests'] = 'Failed basic tests'
        return False
    
    return True
    

def run_integration_tests(node: Node, result: Result) -> bool:
    if not node.integration_tests:
        result.test_results['integration_tests'] = 'skipped'
        return True     # if skipped, still need to proceed to later tasks

    exit_code = run_tests(os.path.join(node.filepath, 'integration'))
    result.test_results['integration_tests'] = 'Passed integration tests'
    if exit_code != pytest.ExitCode.OK:
        result.success = False
        result.test_results['integration_tests'] = 'Failed integration tests'
        return False

    return True


def build_and_test_containers(
        root: Node,
        username: str,
        password: str,
        tag_prefix: str,
        all_info_cmds: dict):

    docker_adapter.login(username, password)

    # search the nodes according to BFS and place into node_order for processing
    

    # load all_info_cmds from spec.yml and pass to wiki operations
    # print(all_info_cmds)

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

    results = []        # no matter success or failure
    full_names = []     # a list of all-success image full names
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
        print(f"****** Building {node.image_name}, (not skipped)")
        image_built, report = docker_adapter.build(node)
        result.container_details['build_log'] = report
        if not image_built:
            result.success = False
            results.append(result)
            continue

        # basic and common tests
        setup_testing_environment(node)
        resp = run_basic_tests(node, result)
        if not resp:
            results.append(result)
            continue

        # push step
        resp, report = docker_adapter.push(node)
        print(f"*** Push image {node.image_name} successfully? {resp}")
        result.container_details['push_success'] = resp
        result.container_details['push_log'] = report
        if not resp:
            result.success = False
            results.append(result)
            continue

        # integration tests
        resp = run_integration_tests(node, result)
        if not resp:
            results.append(result)
            continue

        # update wiki page of individual image that
        #       has been successfully [built, pushed, tested]
        image_obj = docker_adapter.get_image_obj(node)
        if image_obj is not None:
            wiki.write_report(node, all_info_cmds)
        else:
            print(f"*** Unable to get {node.full_image_name}")

        result.success = True
        results.append(result)
        print(f"{node.image_name} reached here")
        full_names.append(result.full_image_name)


    # store results 
    for result in results:
        filename = result.safe_full_image_name
        if 'build_log' in result.container_details:
            build_log = result.container_details.pop('build_log')
            fs.store(filename + '.log', build_log)
        formatted_result = format_result(result)
        resp = fs.store(filename + '.yaml', formatted_result)
        if not resp:
            raise OSError("couldn't store results into artifacts directory")

    # # update Home.md
    wiki.update_Home(images_full_names=full_names, git_short_hash=root.git_suffix)
    

if __name__ == '__main__':
    """Do a test run"""
    get_logger(logging.DEBUG)
    test_spec = {
        'images': {
            'datahub-base-notebook': {
                'build_args': {
                    'PYTHON_VERSION': 'python-3.9.5'
                }
            },
            # 'datascience-notebook': {
            #     'depend_on': 'datahub-base-notebook',
            #     'rebuild': False
            # }
        }
    }

    tree = build_tree(spec_yaml=test_spec, images_changed=[
                      'datahub-base-notebook'], git_suffix='test')

    dockerhub_username = os.environ.get('DOCKERHUB_USERNAME', None)
    dockerhub_token = os.environ.get('DOCKERHUB_TOKEN', None)
    if not dockerhub_username or not dockerhub_token:
        logger.error('dockerhub username or password not set')
        exit(1)

    build_and_test_containers(
        root=tree, username=dockerhub_username, password=dockerhub_token, tag_prefix='test')
