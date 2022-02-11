from sys import path
from termios import VQUIT
from scripts.utils import get_specs, read_var, store_dict, store_var
from scripts.docker_info import get_dependency
from scripts.docker_builder import dbuild
from scripts.docker_tester import _tests_collector
from scripts.docker_pusher import docker_login, push_images
from scripts.utils import get_specs, read_var, store_dict, store_var, read_dict
from scripts.git_helper import get_changed_images
from docker.errors import BuildError
from docker.utils.json_stream import json_stream
from model.spec import BuilderSpec
from typing import List
import docker
import logging
import os
import pytest
from pathlib import Path
from collections import deque
from pydantic import BaseModel

from scripts.dataobjects import build_params_object,imagespec
from model.spec import Buildargs
pjoin = os.path.join

logger = logging.getLogger(__name__)



def test_image(image_tag:str,test_dirs:Path)->None:
    '''
    Test function to runs the test on build image
    Input parameters:
        image_tag: Image which needs to be tested
        test_dirs: Test scripts to be tested
    '''
    print(f'*** Testing {image_tag} ***')
    os.environ['TEST_IMAGE'] = image_tag
    exit_code = pytest.main([
            '-x',       # exit instantly on first error or failed test
            *test_dirs  # test dirs
        ])

    assert exit_code is pytest.ExitCode.OK,f'Image did not pass tests:{image_tag} '
    store_var('IMAGES_TEST_PASSED', image_tag)




class BuildInfo(BaseModel):
    images_changed: str
    git_suffix: str
    build_spec: BuilderSpec
    image_queue: list
    images_built: list = []

class BuildInfoRetrieval:
    def __init__(self, retrieval_func):
        self.retrieval_func = retrieval_func

    def get_info(self) -> BuildInfo:
        return self.retrieval_func()

class BuildInfoStorage:
    def __init__(self, images_built_func):
        self.images_built_func = images_built_func
    
    def store_images_built(self, images_built: List[str]):
        self.images_built_func(images_built)

def store_images_on_filesystem(images_built):
    store_var('IMAGES_BUILT', images)

class ContainerBuilder:
    def __init__(self, container_builder_func):
        self.container_builder_func = container_builder_func
    
    def build_container(self, build_params:Buildargs,stack_dir:str):
        self.container_builder_func(build_params, stack_dir)

def build_units(build_params:Buildargs,stack_dir:str)->None:
    '''
    This Function build image and it dependecies
        build_params:
        stack_dirs:
    '''
    images = []
    for build_param in build_params:
        #image_name, build_path, build_args, plan_name, image_tag = build_param
        print('image building {}'.format(build_param.full_image_tag))
        image, meta = dbuild(
                            path=build_param.imgPath,
                            build_args=build_param.build_args,
                            image_tag=build_param.full_image_tag,
                            nocache=False
                        )
        images.append(build_param.full_image_tag)
        # for image_tag, test_dirs in test_params.items():
        #     test_image(image_tag,test_dirs) 
    return images

class ContainerTester:
    def __init__(self, container_tester_func):
        self.container_tester_func = container_tester_func
    
    def container_test(self, stack_dir, images_built):
        self.container_tester_func(stack_dir, images_built)
    
def container_test(stack_dir, images_built):
    for full_image_tag in images_built:
        test_params = _tests_collector(stack_dir, [full_image_tag])
        for image_tag, test_dirs in test_params.items():
            test_image(image_tag,test_dirs) 

def get_build_info_from_filesystem():
    images_changed = read_var('IMAGES_CHANGED')
    git_suffix = read_var('GIT_HASH_SHORT')
    specs = get_specs(pjoin(stack_dir, 'spec.yml'))
    build_spec = BuilderSpec(specs)
    # need to build the down stream task if parent is changed
    # checking if the depends on image is changing and build 
    # accordingly
    queue = deque(list(build_spec.image_specs.keys()))
    while queue:
        ele = queue.popleft()
        if 'depend_on' in build_spec.image_specs[ele]:
            image_dependecy = build_spec.image_specs[ele]['depend_on']
            if image_dependecy in images_changed:
                images_changed.append(ele)

    return BuildInfo(
        images_changed=images_changed,
        git_suffix=git_suffix,
        build_spec=build_spec,
        image_queue=queue
    )
    

class ContainerPusher:
    def __init__(self, container_pusher_func):
        self.container_pusher_func = container_pusher_func
    
    def push_container(self, images_built: List[str]):
        self.container_pusher_func(images_built)


class ContainerDeleter:
    def __init__(self, container_deleter_func):
        self.container_deleter_func = container_deleter_func
    
    def delete_container(self, images_built):
        self.container_deleter_func(images_built)

def delete_docker_containers(images_built):
    cli.images.prune()
    for tag in images_built:
        cli.images.remove(image=cli.images.get(tag),force=True)

class DockerPusher:
    def __init__(self, dockerhub_token: str, dockerhub_username: str):
        self.dockerhub_token = dockerhub_token
        self.dockerhub_username = dockerhub_username

    def push_container_to_dockerhub(self, images_built):
        cli = docker.from_env()
        if docker_login(cli, self.dockerhub_username, self.dockerhub_token):
            tags = images_built
            pairs = [
                (cli.images.get(tag), tag)
                for tag in tags
            ]
            push_images(cli, pairs)
            return

        raise Exception('Could not push image to dockerhub since login didnt work!')
    
def docker_push_image()->None:
    '''
    Used to push to built image to repository
    1. logging in
    2. reading which variables to push
    3. push images that changed
    4. delete images from filesystem
    '''
    cli = docker.from_env()
    if docker_login(cli, 'etsjenkins', os.environ['DOCKERHUB_TOKEN']):
        tags = read_var('IMAGES_BUILT')
        pairs = [
            (cli.images.get(tag), tag)
            for tag in tags
        ]
        push_images(cli, pairs)
        # delete the local image 
        cli.images.prune()
        for tag in tags:
            cli.images.remove(image=cli.images.get(tag),force=True)

class ContainerFacade:
    def __init__(self, 
                 build_info: BuildInfo, 
                 builder: ContainerBuilder, 
                 tester: ContainerTester, 
                 pusher: ContainerPusher,
                 deleter: ContainerDeleter,
                 build_info_storage: BuildInfoStorage):
        self.build_info = build_info
        self.builder = builder
        self.tester = tester
        self.pusher = pusher
        self.deleter = deleter
        self.build_info_storage = build_info_storage

    def gen_build_params(self, stack_dir) -> [BuildArgs]:
        image_dependecy=None
        if 'depend_on' in self.build_info.build_spec.image_specs[unit_image_name]:
            image_dependecy = self.build_info.build_spec.image_specs[unit_image_name]['depend_on']
        images_to_build=[]
        # check if the depends are built else build
        if image_dependecy not in images_built and image_dependecy is not None:
            # check if image is already in repo and pull if its present
            images_to_build.append(image_dependecy)

        images_to_build.append(unit_image_name)
        # Get the build params for the unit image and its depends
        build_params = self.build_info.build_spec.gen_build_args(
                stack_dir, git_suffix, images_to_build)

        return build_params

    def build_test_push_containers(self, stack_dir):
        for unit_image_name in self.build_info.images_changed: 
            if unit_image_name in images_built:
                continue

            build_params = self.gen_build_params(stack_dir, git_suffix, images_to_build)

            # build
            images_built = self.build_container(build_params,stack_dir)
    
            # store built images
            self.build_info.images_built = images_built
            self.build_info_storage.store_images_built(images_built)

            # test container
            self.container_test(stack_dir, images_built)

            # push the container
            self.push_container(images_built)

            # delete the container
            self.delete_container(images_built)

    def build_container(self, build_params, stack_dir):
        self.builder.build_container(build_params, stack_dir)
        
    def store_images_built(self):
        self.build_info_storage.store_images_built(self.build_info.images_built)

    def container_test(self, stack_dir, images_built):
        self.tester.container_test(stack_dir, images_built)
    
    def push_container(self, images_built):
        self.pusher.push_container(images_built)
    
    def delete_containers(self, images_built):
        self.deleter.delete_container(images_built)


def build_unit(stack_dir: str, container_facade: ContainerFacade) -> None:
    container_facade.build_test_push_containers(stack_dir)


def build_unit(stack_dir:str)->None:
    '''
    Fuction checks for the images that are changed and build them indivisually
    Input Parameters:
        stack_dir:
        
    1. checking images that changed
    2. get the hash
    3. get the build specs and create a dependency queue based off it
    4. build, test, push, delete
    
    '''
    images_changed = read_var('IMAGES_CHANGED')
    git_suffix = read_var('GIT_HASH_SHORT')
    specs = get_specs(pjoin(stack_dir, 'spec.yml'))
    build_spec = BuilderSpec(specs)
    # need to build the down stream task if parent is changed
    # checking if the depends on image is changing and build 
    # accordingly
    queue = deque(list(build_spec.image_specs.keys()))
    while queue:
        ele = queue.popleft()
        if 'depend_on' in build_spec.image_specs[ele]:
            image_dependecy = build_spec.image_specs[ele]['depend_on']
            if image_dependecy in images_changed:
                images_changed.append(ele)
            
    
    #store the images depends that are already built
    images_built = []
    # get the images to build
    for unit_image_name in images_changed:
        # Get all the dependents
        if unit_image_name in images_built:
            continue
        image_dependecy=None
        if 'depend_on' in build_spec.image_specs[unit_image_name]:
            image_dependecy = build_spec.image_specs[unit_image_name]['depend_on']
        images_to_build=[]
        # check if the depends are built else build
        if image_dependecy not in images_built and image_dependecy is not None:
            # check if image is already in repo and pull if its present
            images_to_build.append(image_dependecy)
        
        images_to_build.append(unit_image_name)
        # Get the build params for the unit image and its depends
        build_params = build_spec.gen_build_args(
                stack_dir, git_suffix, images_to_build)
        # Build and test image
        images = build_units(build_params,stack_dir)

        store_var('IMAGES_BUILT', images)
        docker_push_image()
        print(images_to_build)
        #images_built.extend(images_to_build)
    
         
if __name__ == '__main__':
    docker_client=docker.from_env()
    image = dbuild(
        path='images\datahub-base-notebook',
        build_args={'PYTHON_VERSION': 'python-3.8.8'},
        image_tag='base:test',
        docker_client=docker_client
    )
    

    