from sys import path
from scripts.utils import get_specs, read_var, store_dict, store_var
from scripts.docker_info import get_dependency
from scripts.docker_builder import dbuild
from scripts.docker_tester import _tests_collector
from scripts.utils import get_specs, read_var, store_dict, store_var, read_dict
from scripts.git_helper import get_changed_images
from docker.errors import BuildError
from docker.utils.json_stream import json_stream
from model.spec import BuilderSpec
import docker
from collections import namedtuple
import time
import logging
import itertools
import re
import os
from typing import NamedTuple
import pytest
pjoin = os.path.join

logger = logging.getLogger(__name__)

def build_units(build_params,stack_dir):
    '''
    This Function build image and it dependecies
        build_params:
        stack_dirs:
    '''
    for build_param in build_params:
        image_name, build_path, build_args, plan_name, image_tag = build_param
        print('image building {}'.format(image_name))
        image, meta = dbuild(
                            path=build_path,
                            build_args=build_args,
                            image_tag=image_tag,
                            nocache=False
                        )
        # test_params = _tests_collector(stack_dir, [image_tag])
        # for image_tag, test_dirs in test_params.items():
        #     test_image(image_tag,test_dirs) 

def test_image(image_tag,test_dirs):
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


def build_unit(stack_dir):
    '''
    Fuction checks for the images that are changed and build them indivisually
    Input Parameters:
        stack_dir: 
    
    '''
    images_changed = read_var('IMAGES_CHANGED')
    git_suffix = read_var('GIT_HASH_SHORT')
    specs = get_specs(pjoin(stack_dir, 'spec.yml'))
    build_spec = BuilderSpec(specs)
    # store the images depends that are already built
    images_built = []
    # get the images to build
    for unit_image_name in images_changed:
        # Get all the dependents
        image_dependecy = build_spec.image_specs[unit_image_name]['depend_on']
        images_to_build=[]
        # check if the depends are built else build
        if image_dependecy not in images_built:
            images_to_build.append(image_dependecy)
        images_to_build.append(unit_image_name)
        # Get the build params for the unit image and its depends
        build_params = build_spec.gen_build_args(
                stack_dir, git_suffix, images_to_build)
        # Build and test image
        print(build_params)
        build_units(build_params,stack_dir)
         
if __name__ == '__main__':
    docker_client=docker.from_env()
    image = dbuild(
        path='images\datahub-base-notebook',
        build_args={'PYTHON_VERSION': 'python-3.8.8'},
        image_tag='base:test',
        docker_client=docker_client
    )
    

    