from scripts.utils import get_logger
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from io import StringIO
import os
import yaml
import pytest
import logging
import sys


from scripts.tree import Node, build_tree, load_spec
from scripts import docker_adapter
from scripts import fs
from scripts import wiki
from scripts.utils import convert_size

logger = get_logger()


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


def run_tests(testdirs: List[str], pytest_exec=pytest.main) -> Tuple[pytest.ExitCode, str]:
    # https://stackoverflow.com/questions/47784802/output-stdio-and-stderr-from-pytest-main
    try:
        original_output = sys.stdout
        sys.stdout = StringIO()

        exit_code = pytest_exec([
            '-x',
            *testdirs
        ])

        output = sys.stdout.getvalue()

    except Exception as e:
        logging.error(f'Failed to execut pytests; {e}')
        return pytest.ExitCode.TESTS_FAILED, ''
    finally:
        sys.stdout.close()
        sys.stdout = original_output

    return exit_code, output


def get_basic_test_locations(node: Node, stackdir='images', test_common_dirname='tests_common') -> List[str]:
    if not node.filepath:
        raise RunTestError(f'Must specify node.filepath for {node}')
    common_tests = os.path.join(stackdir, test_common_dirname)
    return [common_tests, os.path.join(node.filepath, 'test')]


def setup_testing_environment(node: Node):
    os.environ['TEST_IMAGE'] = node.image_name + ':' + node.image_tag


def run_basic_tests(node: Node, result: Result) -> bool:
    if not os.environ.get('TEST_IMAGE', None):
        raise RunTestError(
            'You must specify TEST_IMAGE envar before running tests')
    test_locations = get_basic_test_locations(node)
    exit_code, report = run_tests(test_locations)

    result.test_results['basic_tests'] = 'Passed basic tests'
    result.test_results['test_log'] = report
    if exit_code != pytest.ExitCode.OK and exit_code != pytest.ExitCode.NO_TESTS_COLLECTED:
        result.success = False
        result.test_results['basic_tests'] = 'Failed basic tests'
        return False

    return True


def run_integration_tests(node: Node, result: Result) -> bool:
    if not node.integration_tests:
        result.test_results['integration_tests'] = 'skipped'
        return True     # if skipped, still need to proceed to later tasks

    exit_code, report = run_tests(
        # run_tests() takes a list of dir
        [ os.path.join(node.filepath, 'integration_tests') ]     
    )
    result.test_results['integration_tests'] = 'Passed integration tests'
    result.test_results['test_log'] = report
    if exit_code != pytest.ExitCode.OK and exit_code != pytest.ExitCode.NO_TESTS_COLLECTED:
        result.success = False
        result.test_results['integration_tests'] = 'Failed integration tests'
        return False

    return True


def build_and_test_containers(
        root: Node,
        username: str,
        password: str,
        tag_prefix: str,
        all_info_cmds: dict) -> bool:
    """Goal:
    given the root of build-and-test tree, traverse the tree and do the following
    to each node (represents an image) on-the-fly:
        * determine if the node needs to be rebuilt. If YES:
        - build the image
        - run common tests (located in /images/tests_common)
        - push to dockerhub
        - run integration tests (more complex Selenium/gRPC tests)
        - update wiki page (a .md of this particular image)
        * no matter success or failure, reclaim space (docker cache)

    General Structure:
    1. (while q:) traverse tree (with BFS) and place nodes into node_order for processing
    2. (for node in node_order:) major loop that does 'everything' for each node
    3. (for result in results:) store logs in .yml format to build_artifacts
    4. update **the local copy** of Home.md; see its function doc
    5. return (bool) all_pass

    Note:
        For each node, if any of the "- step" fails, those after it would not be executed.
        But this will not affect other images. 

    Args:
        root (Node): (for now) always datahub-base-notebook
        username (str): docker username, passed in as env variable
        password (str): docker token, passed in as env variable
        tag_prefix (str): e.g. '2023.2', defined in and loaded from spec.yml
        all_info_cmds (dict): also see spec.yml

    Returns:
        bool: whether ALL images in the tree pass, where "pass" means either of
            - no need to rebuild
            - rebuilt, tested, cmds executed, logs and wiki written.
    """

    docker_adapter.login(username, password)

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

    # temp fix: base/parent should be built whenever >=1 child is built
    # since we use {BASE_TAG}-{GIT_HASH} as tag
    # ONLY works for our single-level dependency
    if any(node.rebuild for node in node_order):
        # this is root.
        if not node_order[0].rebuild:
            node_order[0].rebuild = True
            logger.info(f"Root/Base image {root.image_name} has to be rebuilt due to child change.")

    results = []        # no matter success or failure
    full_names = []     # a list of all-success image full names
    for node in node_order:
        try:
            logger.info(f'Processing node = {node.image_name}')

            result = Result(full_image_name=node.image_name +
                            ':' + node.image_tag)

            # flow-control boolean; cannot `continue` since we need prune (reclaim space)
            fail_and_stop = False 

            # safe short-circuiting when no rebuild needed
            if not node.rebuild:
                logger.info(f"skipping node {node.image_name}")
                result.container_details['image_built'] = False
                full_names.append(result.full_image_name)
                continue         

            # build image
            print(f"****** Building {node.image_name}, (not skipped)")
            image_built, report = docker_adapter.build(node)
            result.container_details['image_built'] = image_built
            result.container_details['build_log'] = report
            if not image_built:
                logger.error(f"couldn't build {node.full_image_name}")
                fail_and_stop = True
                break
            else:
                logger.info(f"successfully built {node.full_image_name}")
        
            # basic and common tests
            logger.info(f"Testing {node.full_image_name}")
            setup_testing_environment(node)
            resp = run_basic_tests(node, result)
            if 'test_log' in result.test_results:
                logger.debug(result.test_results['test_log'])
            if not resp:
                fail_and_stop = True
                logger.error(f"{node.full_image_name} failed common tests")
                break
            else:
                logger.info(f"{node.full_image_name} passed common tests")


            # push step
            resp, report = docker_adapter.push(node)
            result.container_details['push_success'] = resp
            result.container_details['push_log'] = report
            if not resp:
                fail_and_stop = True
                logger.error(f"couldn't push {node.full_image_name}")
                break
            else:
                logger.info(f"{node.full_image_name} pushed successfully")


            # integration tests
            resp = run_integration_tests(node, result)
            if not resp:
                logger.error(f"{node.full_image_name} failed integration test")
                fail_and_stop = True
                break
            else:
                logger.info(f"{node.full_image_name} passed integration tests (or don't have any)")

            # update wiki page of individual image that
            #       has been successfully [built, pushed, tested]
            image_obj = docker_adapter.get_image_obj(node)
            if image_obj is None:
                logger.error(f"*** Unable to get {node.full_image_name}")
                fail_and_stop = True
                break  
            else:
                wiki.write_report(node, image_obj, all_info_cmds)
                logger.info(f"{node.full_image_name} wiki page is created")

            # if all-passed, the image should appear on Home.md
            logger.info(f"{node.full_image_name} will appear on Home.md")
            full_names.append(result.full_image_name)

        except Exception as e:
            logger.error(f"Uncaught exception during container_build_and_test loop; {e}")
        finally:
            # Conclude the build-test-push-wiki result for this image
            result.success = not fail_and_stop
            results.append(result)
            logger.info(f"*** Build-and-Test main loop: {node.image_name} success ? {result.success}")

            if result.container_details['image_built']:
                # delete cache and reclaim space
                space_reclaimed = convert_size(docker_adapter.prune(node.full_image_name))
                logger.info(f"Reclaimed {space_reclaimed} from pruning docker")
        ### EXIT main loop ###

    # store results 
    for result in results:
        try:
            filename = result.safe_full_image_name
            if 'build_log' in result.container_details:
                build_log = result.container_details.pop('build_log')
                fs.store(filename + '.build.log', build_log, fs.LOGS_PATH)
            
            if 'test_log' in result.test_results:
                test_log = result.test_results.pop('test_log')
                fs.store(filename + '.basic-tests.log', test_log, fs.LOGS_PATH)
        
            formatted_result = format_result(result)
            resp = fs.store(filename + '.yaml', formatted_result)
        except Exception as e:
            logger.error(f"couldn't store result of {filename} into artifacts directory, \nerror is {e}")

    # # update Home.md
    wiki.update_Home(images_full_names=full_names, git_short_hash=root.git_suffix)
    logger.info("home.md updated")

    # only all_pass images in full_names; all images in results
    return len(full_names) == len(results)

    

if __name__ == '__main__':
    """Do a test run"""
    get_logger(logging.DEBUG)
    test_spec = {
        'images': {
            'datahub-base-notebook': {
                'build_args': {
                    'PYTHON_VERSION': 'python-3.9.5'
                },
                'info_cmds': [
                    'PY_VER',
                    'CONDA_INFO',
                    'CONDA_LIST'
                ]
            },
            # 'datascience-notebook': {
            #     'depend_on': 'datahub-base-notebook',
            #     'rebuild': False
            # }
        }
    }

    all_info_cmds = {
            'PY_VER': {
                'description': 'Python Version',
                'command': 'python --version'
            },
            'CONDA_INFO': {
                'description': 'Conda Info',
                'command': 'conda info'
            },
            'CONDA_LIST': {
                'description': 'Conda Packages',
                'command': 'conda list'
            },
        }

    tree = build_tree(spec_yaml=test_spec, images_changed=[
                      'datahub-base-notebook'], git_suffix='test')

    dockerhub_username = os.environ.get('DOCKERHUB_USERNAME', None)
    dockerhub_token = os.environ.get('DOCKERHUB_TOKEN', None)
    if not dockerhub_username or not dockerhub_token:
        logger.error('dockerhub username or password not set')
        exit(1)
    
    if not os.path.exists('manifests'):
        logger.error('You must have a manifests/ directory at this root')
        exit(1)

    build_and_test_containers(
        root=tree, username=dockerhub_username, password=dockerhub_token, tag_prefix='test', all_info_cmds=all_info_cmds)
