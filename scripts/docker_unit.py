from sys import path
from termios import VQUIT
from scripts.utils import get_specs, read_var, store_dict, store_var
from scripts.docker_builder import dbuild
from scripts.docker_tester import _tests_collector
from scripts.docker_pusher import docker_login, push_images
from scripts.utils import get_specs, read_var, store_dict, store_var, read_dict
from scripts.git_helper import get_changed_images
from docker.errors import BuildError
from docker.utils.json_stream import json_stream
from model.spec import BuilderSpec
from typing import Dict, List
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



def image_test(image_tag:str,test_dirs:Path)->None:
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
    if exit_code is pytest.ExitCode.NO_TESTS_COLLECTED:
        ## used in testing 
        store_var('IMAGES_TEST_PASSED', image_tag)
        return
    assert exit_code is pytest.ExitCode.OK ,f'Image did not pass tests:{image_tag} '
    store_var('IMAGES_TEST_PASSED', image_tag)




class BuildInfo(BaseModel):
    images_changed: List[str]=[]
    git_suffix: str
    build_spec: BuilderSpec
    image_queue: deque
    images_built: List[str] =[]
    class Config:
        arbitrary_types_allowed = True


class BuildInfoRetrieval:
    def __init__(self, retrieval_func):
        self.retrieval_func = retrieval_func

    def get_info(self,stack_dir) -> BuildInfo:
        return self.retrieval_func(stack_dir)

class BuildInfoStorage:
    def __init__(self, images_built_func):
        self.images_built_func = images_built_func
    
    def store_images_built(self, images_built: List[str]):
        self.images_built_func(images_built)

def store_images_on_filesystem(images_built):
    store_var('IMAGES_BUILT', images_built)

class ContainerBuilder:
    def __init__(self, container_builder_func):
        self.container_builder_func = container_builder_func
    
    def build_container(self, build_params:Buildargs,stack_dir:str):
        return self.container_builder_func(build_params, stack_dir)

def build_units(build_params:Buildargs,stack_dir:str)->Dict:
    '''
    This Function build image and it dependecies
        build_params:
        stack_dirs:
    '''
    images = {}
    for build_param in build_params:
        #image_name, build_path, build_args, plan_name, image_tag = build_param
        print('image building {}'.format(build_param.full_image_tag))
        image, meta = dbuild(
                            path=build_param.imgPath,
                            build_args=build_param.build_args,
                            image_tag=build_param.full_image_tag,
                            nocache=False
                        )
        images[build_param.imgDef] = build_param.full_image_tag     
    return images

class ContainerTester:
    def __init__(self, container_tester_func):
        self.container_tester_func = container_tester_func
    
    def container_test(self, stack_dir, images_built,dry_run=False):
        return self.container_tester_func(stack_dir, images_built,dry_run)
    
def container_test(stack_dir, images_built,dry_run=False):
    #for full_image_tag in images_built:
    test_params = _tests_collector(stack_dir, images_built)
    print(f"*** In container_test, the Dict test_params is {test_params}")
    if not dry_run:
        for image_tag, test_dirs in test_params.items():
            image_test(image_tag,test_dirs)
    return test_params

def get_build_info_from_filesystem(stack_dir:str,spec_file='spec.yml')->BuildInfo:
    images_changed = read_var('IMAGES_CHANGED')
    git_suffix = read_var('GIT_HASH_SHORT')
    if git_suffix is None:
        git_suffix = ''
    specs = get_specs(pjoin(stack_dir,spec_file ))
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
    if len(images_changed)==0:
        images_changed =[]

    return BuildInfo(
        images_changed=images_changed,
        git_suffix=git_suffix,
        build_spec=build_spec,
        image_queue=queue
    )
    

class ContainerPusher:
    def __init__(self, container_pusher_func):
        self.container_pusher_func = container_pusher_func
    
    def push_container(self, images_built: List[str], untested = False):
        self.container_pusher_func(images_built, untested)


class ContainerDeleter:
    def __init__(self, container_deleter_func):
        self.container_deleter_func = container_deleter_func
    
    def delete_container(self, images_built):
        self.container_deleter_func(images_built)

def delete_docker_containers(images_built):
    cli = docker.from_env()
    for tag in images_built:
        cli.images.remove(image=tag,force=True)
    cli.images.prune({'dangling':True})

class DockerPusher:
    def __init__(self, dockerhub_token: str, dockerhub_username: str):
        self.dockerhub_token = dockerhub_token
        self.dockerhub_username = dockerhub_username

    def push_container_to_dockerhub(self, images_built, untested):
        cli = docker.from_env()
        if docker_login(cli, self.dockerhub_username, self.dockerhub_token):
            tags = images_built
            pairs = [
                (cli.images.get(tag), tag)
                for tag in tags
            ]
            push_images(cli, pairs, untested)
            return

        raise Exception('Could not push image to dockerhub since login didnt work!')
    
# def docker_push_image()->None:
#     '''
#     Used to push to built image to repository
#     1. logging in
#     2. reading which variables to push
#     3. push images that changed
#     4. delete images from filesystem
#     '''
#     cli = docker.from_env()
#     if docker_login(cli, os.environ['DOCKERHUB_USER'], os.environ['DOCKERHUB_TOKEN']):
#         tags = read_var('IMAGES_BUILT')
#         pairs = [
#             (cli.images.get(tag), tag)
#             for tag in tags
#         ]
#         # delete the local image 
#         cli.images.prune()
#         for tag in tags:
#             cli.images.remove(image=cli.images.get(tag),force=True)
        

class ContainerFacade:
    def __init__(self, 
                 build_info_retrieval: BuildInfoRetrieval, 
                 builder: ContainerBuilder, 
                 tester: ContainerTester, 
                 pusher: ContainerPusher,
                 deleter: ContainerDeleter,
                 build_info_storage: BuildInfoStorage):
        self.build_info_retrieval = build_info_retrieval
        self.builder = builder
        self.tester = tester
        self.pusher = pusher
        self.deleter = deleter
        self.build_info_storage = build_info_storage

    def gen_build_params(self, stack_dir, unit_image_name:str) :#-> [BuildArgs]:
        build_info = self.build_info_retrieval.get_info(stack_dir)
        image_dependecy=None
        if 'depend_on' in build_info.build_spec.image_specs[unit_image_name]:
            # also a str
            image_dependecy = build_info.build_spec.image_specs[unit_image_name]['depend_on']
        
        images_to_build=[]
        # check if the depends are built else build
        if  image_dependecy is not None:
            pass    # should the dep (parent image) also be built?
            # # check if image is already in repo and pull if its present
            # images_to_build.append(image_dependecy)

        images_to_build.append(unit_image_name)
        # Get the build params for the unit image and its depends
        build_params = build_info.build_spec.gen_build_args(
                stack_dir, build_info.git_suffix, images_to_build)

        return build_params,image_dependecy

    def build_test_push_containers(self, stack_dir):
        build_info = self.build_info_retrieval.get_info(stack_dir)
        all_image_built = {}
        image_dependency={}
        # unit_image_name: str
        print(f"***CheckThis***, {set(build_info.images_changed)}")
        for unit_image_name in set(build_info.images_changed): 
            if unit_image_name in build_info.images_built:
                continue
            
            # get build parameters of this single image
            build_params,dependency = self.gen_build_params(stack_dir,unit_image_name)
            image_dependency[unit_image_name] = dependency


            
            # build
            images_built = self.build_container(build_params,stack_dir)
    
            # store built images
            build_info.images_built = list(images_built.values())
            all_image_built.update(images_built)
            self.build_info_storage.store_images_built(list(images_built.values()))
            
            # push externally tested images
            self.push_untested_container(build_info.images_built)

            # test container
            
            #if any(['ucsdets/rstudio-notebook' in i for i in  build_info.images_built]):
            print(f"*** Looking at unit image (on line 273 for loop) {unit_image_name}, \
                build_info.images_built is {build_info.images_built}")
            self.container_test(stack_dir, build_info.images_built)

            # push the container
            self.push_container(build_info.images_built)

            # delete the container
            
            self.delete_containers(build_info.images_built)
            
        
        # Storing the tags of the images built used in down stream task as inputs 
        self.build_info_storage.store_images_built(list(all_image_built.values()))
        images_dep = {}
        for image,dep in image_dependency.items():
            if dep is None:
                continue
            images_dep[all_image_built[image]]=all_image_built[dep]
        store_dict('image-dependency.json', images_dep)
    
    
    def build_container(self, build_params, stack_dir):
        return self.builder.build_container(build_params, stack_dir)
        
    def store_images_built(self):
        self.build_info_storage.store_images_built(self.build_info_retrieval.images_built)

    def push_untested_container(self, images_built):
        self.pusher.push_container(images_built, True)

    def container_test(self, stack_dir, images_built):
        self.tester.container_test(stack_dir, images_built)
    
    def push_container(self, images_built):
        self.pusher.push_container(images_built)
    
    def delete_containers(self, images_built):
        self.deleter.delete_container(images_built)


def build_unit(stack_dir: str, container_facade: ContainerFacade) -> None:
    container_facade.build_test_push_containers(stack_dir)


# def build_unit(stack_dir:str)->None:
#     '''
#     Fuction checks for the images that are changed and build them indivisually
#     Input Parameters:
#         stack_dir:
        
#     1. checking images that changed
#     2. get the hash
#     3. get the build specs and create a dependency queue based off it
#     4. build, test, push, delete
    
#     '''
#     images_changed = read_var('IMAGES_CHANGED')
#     git_suffix = read_var('GIT_HASH_SHORT')
#     specs = get_specs(pjoin(stack_dir, 'spec.yml'))
#     build_spec = BuilderSpec(specs)
#     # need to build the down stream task if parent is changed
#     # checking if the depends on image is changing and build 
#     # accordingly
#     queue = deque(list(build_spec.image_specs.keys()))
#     while queue:
#         ele = queue.popleft()
#         if 'depend_on' in build_spec.image_specs[ele]:
#             image_dependecy = build_spec.image_specs[ele]['depend_on']
#             if image_dependecy in images_changed:
#                 images_changed.append(ele)
            
    
#     #store the images depends that are already built
#     images_built = []
#     # get the images to build
#     for unit_image_name in images_changed:
#         # Get all the dependents
#         if unit_image_name in images_built:
#             continue
#         image_dependecy=None
#         if 'depend_on' in build_spec.image_specs[unit_image_name]:
#             image_dependecy = build_spec.image_specs[unit_image_name]['depend_on']
#         images_to_build=[]
#         # check if the depends are built else build
#         if image_dependecy not in images_built and image_dependecy is not None:
#             # check if image is already in repo and pull if its present
#             images_to_build.append(image_dependecy)
        
#         images_to_build.append(unit_image_name)
#         # Get the build params for the unit image and its depends
#         build_params = build_spec.gen_build_args(
#                 stack_dir, git_suffix, images_to_build)
#         # Build and test image
#         images = build_units(build_params,stack_dir)

#         store_var('IMAGES_BUILT', images)
#         docker_push_image()
#         print(images_to_build)
#         #images_built.extend(images_to_build)

def setup_pusher_func(dockerhub_user, dockerhub_token):
    def pusher_func(images_built: List[str], untested = False):
        docker_pusher = DockerPusher(dockerhub_token,dockerhub_user)
        return docker_pusher.push_container_to_dockerhub(images_built, untested)
    return pusher_func
         
if __name__ == '__main__':
    docker_client=docker.from_env()
    image = dbuild(
        path='images\datahub-base-notebook',
        build_args={'PYTHON_VERSION': 'python-3.8.8'},
        image_tag='base:test',
        docker_client=docker_client
    )
    

    