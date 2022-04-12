from gc import collect
import os
import sys
import json
sys.path.append('.')
from scripts.docker_unit  import *
from scripts.utils import store_var, read_var
import pytest
from unittest.mock import MagicMock
from scripts.docker_tester import run_test
import docker

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
    '''
    Test case for checking the build info
    '''
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
    '''
    Test case for testing the build 
    '''
    store_var('IMAGES_CHANGED', imgs_changed)
    build_info = get_build_info_from_filesystem(stack_dir)
    #print(build_info.images_changed)
    build_params = build_info.build_spec.gen_build_args(
                stack_dir, build_info.git_suffix, build_info.images_changed)
    build = ContainerBuilder(build_units)
    collected = build.build_container(build_params,stack_dir)
    assert list(collected.values()) == expected_items

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
    '''
    Test case for  
    '''
    store_var('IMAGES_BUILT', imgs_built)
    tester = ContainerTester(container_tester_func=container_test)
    collected = tester.container_test(stack_dir, imgs_built,dry_run=True)
    #print(collected == expected_items)
    assert collected == expected_items

@pytest.mark.push
@pytest.mark.parametrize(
        "stack_dir,imgs_built,expected_items",
        [
            (
                "tests/data/stack_5",
                ['base'],
                [ 'sumukhbadam/base:latest','sumukhbadam/branch:latest', 'sumukhbadam/leaf:latest']
            ),
        ],
    )
def test_push_container(stack_dir,imgs_built,expected_items):
    store_var('IMAGES_CHANGED', imgs_built)
    build_info = get_build_info_from_filesystem(stack_dir)
    build_params = build_info.build_spec.gen_build_args(
                stack_dir, build_info.git_suffix, build_info.images_changed)
    build = ContainerBuilder(build_units)
    collected = build.build_container(build_params,stack_dir)
    with open('./tests/cred.json','r') as ftp:
        data = json.load(ftp)
    pusher = DockerPusher(data['DOCKERHUB_TOKEN'],data['DOCKERHUB_USERNAME'])
    docker_push = ContainerPusher(pusher.push_container_to_dockerhub)
    docker_push.push_container(list(collected.values()))
    cli = docker.from_env()
    images_pushed = []
    for i in expected_items:
        repo,tag = i.split(':')
        images_pushed.extend(cli.images.pull(repo,tag).tags)
    assert all( [i in images_pushed for i in expected_items]) 


@pytest.mark.parametrize(
        "imgs_built,expected_items",
        [
            (
                [ 'fakeuser/base:latest','fakeuser/branch:latest','fakeuser/leaf:latest'],
                [ 'fakeuser/base:latest','fakeuser/branch:latest', 'fakeuser/leaf:latest']
            ),
        ],
    )
def test_delete_container(imgs_built,expected_items):
    store_var('IMAGES_BUILT', imgs_built)
    delete_function = ContainerDeleter(container_deleter_func=delete_docker_containers)
    delete_function.delete_container(imgs_built)
    collected=[]
    cli =  docker.from_env()
    for i in cli.images.list():
        for j in i.tags:
                collected.append(j)
    assert all([i not in collected for i in expected_items])
