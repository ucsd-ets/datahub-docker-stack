import os
pjoin = os.path.join
from shutil import rmtree
from doit import get_var

from scripts.git_helper import save_changed_images, save_git_info
from scripts.docker_builder import run_build
from scripts.docker_untested_pusher import run_untested_push
from scripts.docker_tester import run_test
from scripts.docker_pusher import run_push
from scripts.docker_tagger import run_tagging
from scripts.manifests import run_manifests, run_stable_manifests
from scripts.docker_unit import *


import pytest
import requests


DOIT_CONFIG = dict(
    verbosity=2
)

# get_var(<key>, <default_val>)
USE_STACK = get_var('stack_dir', 'images')

def task_unit_build():
    """Build docker image and test it unit wise"""
    # at runtime, configure real objects
    build_retrieval = BuildInfoRetrieval(retrieval_func=get_build_info_from_filesystem)
    build_info_storage = BuildInfoStorage(images_built_func=store_images_on_filesystem)
    container_builder = ContainerBuilder(container_builder_func=build_units)
    container_tester = ContainerTester(container_tester_func=container_test)
    pusher_func=setup_pusher_func("etsjenkins", os.environ['DOCKERHUB_TOKEN'])
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
    
    return {
        'actions':[build_unit],
        'file_dep': ['artifacts/IMAGES_CHANGED'],
        'targets': ['artifacts/builder-metainfo_unit.json', 'artifacts/IMAGES_BUILT_unit'],
        'params':[
            {
                'name': 'stack_dir',
                'short': 'd',
                'long': 'stack_dir',
                'default': 'images'
            },
            {
                'name': 'container_facade',
                'short': 'c',
                'long': 'container_facade',
                'default': container_facade
            }
        ],

    }

def task_prep():
    """Prep directory for logs and artifacts"""

    def _prep():
        if not os.path.exists('artifacts'):
            os.mkdir('artifacts')
            open(pjoin('artifacts', '.empty'), 'a').close()
        if not os.path.exists('logs'):
            os.mkdir('logs')
            open(pjoin('logs', '.empty'), 'a').close()
        if not os.path.exists('manifests'):
            os.mkdir('manifests')
            open(pjoin('manifests', '.empty'), 'a').close()

    return {
        'actions': [_prep],
        'targets': ['artifacts/.empty', 'logs/.empty', 'manifests/.empty']
    }

def task_clear():

    def _clear():
        if os.path.exists('artifacts'):
            rmtree('artifacts')
        if os.path.exists('logs'):
            rmtree('logs')
    
    return {
        'actions': [_clear]
    }

def task_prebuild():
    """Prepare a build stack"""
    return {
        'actions': [save_changed_images, save_git_info],
        'file_dep': ['artifacts/.empty', 'logs/.empty'],
        'targets': ['artifacts/IMAGES_CHANGED', 'artifacts/GIT_*']
    }

def task_untested_push():
    """Push all built images that need testing elsewhere"""
    return {
        'actions': [run_untested_push],
        'file_dep': ['artifacts/IMAGES_BUILT'],
        'targets': ['artifacts/IMAGES_UNTESTED_PUSHED']
    }


def task_push():
    """Push all built images"""
    return {
        'actions': [run_push],
        'file_dep': ['artifacts/IMAGES_BUILT'],
        'targets': ['artifacts/IMAGES_PUSHED']
    }


def task_manifest():
    """Build image manifests for all built images"""
    return {
        'actions': [run_manifests],
        'file_dep': ['artifacts/IMAGES_BUILT'],
        'targets': ['manifests/*.md'],
        'params':[
            {
                'name': 'stack_dir',
                'short': 'd',
                'long': 'stack_dir',
                'default': 'images'
            },
        ],
    }

def task_tag():
    """Tag and push images with new tags"""
    return {
        'actions': [run_tagging],
        'uptodate': [False],
        'file_dep': ['artifacts/.empty', 'logs/.empty'],
        'targets': ['artifacts/IMAGES_TAGGED'],
        'params':[
            {
                'name': 'commit_tag',
                'long': 'commit_tag',
                'default': None
            },
            {
                'name': 'keyword',
                'long': 'keyword',
                'default': None
            },
            {
                'name': 'tag_replace',
                'long': 'tag_replace',
                'default': None
            },
            {
                'name': 'dry_run',
                'short': 's',
                'long': 'dry_run',
                'default': False
            },
        ],
    }


def task_stable():
    """Build image manifests for all stable tagged images"""
    return {
        'actions': [run_stable_manifests]
    }
