import os
import sys
sys.path.append('.')
from scripts.docker_unit import *
from scripts.utils import store_var, read_var
import pytest
from unittest.mock import MagicMock
from scripts.docker_tester import run_test

# @pytest.fixture()
# def setup_container_facade_for_testing():
#     # setup fake buildinforetrieval
#     mock_build_info = BuildInfo(
#         images_changed=['im1', 'im2'],
#         git_suffix='mysuffix'
#     )

#     get_build_info_from_filesystem = MagicMock(return_value=BuildInfo)
#     build_retrieval = BuildInfoRetrieval(retrieval_func=get_build_info_from_filesystem)

#     store_images_on_filesystem = MagicMock()
#     build_units = MagicMock()
#     container_test = MagicMock()
#     container_push = MagicMock()
#     container_delete = MagicMock()

#     build_info_storage = BuildInfoStorage(images_built_func=store_images_on_filesystem)
#     container_builder = ContainerBuilder(container_builder_func=build_units)
#     container_tester = ContainerTester(container_tester_func=container_test)
#     container_pusher = ContainerPusher(container_pusher_func=container_push)
#     container_deleter = ContainerDeleter(container_deleter_func=container_delete)

#     container_facade = ContainerFacade(
#         build_retrieval,
#         container_builder,
#         container_tester,
#         container_pusher,
#         container_deleter,
#         build_info_storage
#     )

# def test_container_facade_build_container():
#     pass

@pytest.mark.parametrize(
        "stack_dir,imgs_changed,expected_items",
        [
            (
                "tests/data/stack_0", ['base'], 
                ['base', 'branch', 'leaf']
            ),
        ],
    )
def test_build_info(stack_dir,imgs_changed,expected_items):
    store_var('IMAGES_CHANGED', imgs_changed)
    build_info = get_build_info_from_filesystem(stack_dir)
    assert build_info.images_changed == expected_items
@pytest.mark.parametrize(
        "stack_dir,imgs_changed,expected_items",
        [
            (
                "tests/data/stack_0", ['base'], 
                ['fakeuser/base:latest', 'fakeuser/branch:latest', 'fakeuser/leaf:latest']
            ),
        ],
    )
def test_container_build(stack_dir,imgs_changed,expected_items):
    store_var('IMAGES_CHANGED', imgs_changed)
    build_info = get_build_info_from_filesystem(stack_dir)
    print(build_info.images_changed)
    build_params = build_info.build_spec.gen_build_args(
                stack_dir, build_info.git_suffix, build_info.images_changed)
    build = ContainerBuilder(build_units)
    collected = build.build_container(build_params,stack_dir)
    assert collected == expected_items

@pytest.mark.parametrize(
        "stack_dir,imgs_built,expected_items",
        [
            (
                "tests/data/stack_2", 
                [ 'fakeuser/base:latest','fakeuser/branch:latest', 'fakeuser/leaf:latest'],
                {
                    'fakeuser/base:latest': [
                        'tests/data/stack_2/tests_common',
                        'tests/data/stack_2/base/test'
                    ],
                    'fakeuser/branch:latest': [
                        'tests/data/stack_2/tests_common',
                        'tests/data/stack_2/branch/test',
                        'tests/data/stack_2/base/test'
                    ],
                    'fakeuser/leaf:latest': [
                        'tests/data/stack_2/tests_common',
                        'tests/data/stack_2/leaf/test',
                        'tests/data/stack_2/branch/test',
                        'tests/data/stack_2/base/test'
                    ]
                }
            ),
        ],
    )
def test_container_tester(stack_dir,imgs_built,expected_items):
    store_var('IMAGES_BUILT', imgs_built)
    tester = ContainerTester(container_tester_func=container_test)
    collected = tester.container_test(stack_dir, imgs_built)
    assert collected == expected_items

@pytest.mark.parametrize(
        "imgs_built,expected_items",
        [
            (
                [ 'fakeuser/base:latest','fakeuser/branch:latest', 'fakeuser/leaf:latest'],
                [ 'fakeuser/base:latest','fakeuser/branch:latest', 'fakeuser/leaf:latest']
            ),
        ],
    )
def test_delete_container(imgs_built,expected_items):
    store_var('IMAGES_BUILT', imgs_built)
    delete_function = ContainerDeleter(container_deleter_func=delete_docker_containers)
    delete_function.delete_container(imgs_built)
    collected = read_var('IMAGE_REMOVED')
    assert collected == expected_items


"""
TODO
1. either modify or copy stack_2 to:
    1.1. Reference image_name to an actual pushable docker image_name/tag. e.g. ucsdets/datahub-docker-stacks-test-img-1
2. point the build_unit function to stack defined in step 1.
3. run the build_unit function and test for:
    3.1. containers are pullable from dockerhub
    3.2. containers have deleted from the local filesystem 
"""

@pytest.mark.integration
def test_build_unit():
    build_retrieval = BuildInfoRetrieval(retrieval_func=get_build_info_from_filesystem)
    build_info_storage = BuildInfoStorage(images_built_func=store_images_on_filesystem)
    container_builder = ContainerBuilder(container_builder_func=build_units)
    container_tester = ContainerTester(container_tester_func=container_test)

    container_pusher = ContainerPusher(container_pusher_func=pusher_func)
    container_deleter = ContainerDeleter(container_deleter_func=delete_docker_containers)

    container_facade = ContainerFacade(
        build_retrieval,
        container_builder,
        container_tester,
        container_pusher,
        container_deleter,
        build_info_storage
    )

    # initialize stack_dir
    # run the thing
    assert False

# def test_container_facade_container_test():
#     get_build_info_from_filesystem = MagicMock()
#     store_images_on_filesystem = MagicMock()
#     build_units = MagicMock()
#     container_test = MagicMock()
    
#     build_retrieval = BuildInfoRetrieval(retrieval_func=get_build_info_from_filesystem)
#     build_info_storage = BuildInfoStorage(images_built_func=store_images_on_filesystem)
#     container_builder = ContainerBuilder(container_builder_func=build_units)
#     container_tester = ContainerTester(container_tester_func=container_test)
    

    
#     container_pusher = ContainerPusher
    
#     container_facade = ContainerFacade(
#         build_retrieval,
#         container_builder,
#         container_tester,
#         build_info_storage
#     )

#     stack_dir = '/dir'
#     images_built = ['fakeimages']
#     container_facade.container_test(stack_dir, images_built)
#     container_test.assert_called_with(stack_dir, images_built)
    

