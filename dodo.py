import os
pjoin = os.path.join
from shutil import rmtree
from doit import get_var

from scripts.git_helper import save_changed_images, save_git_info
from scripts.docker_builder import run_build
from scripts.docker_tester import run_test
from scripts.docker_pusher import run_push
from scripts.docker_tagger import run_tagging
from scripts.manifests import run_manifests, run_stable_manifests

import pytest


DOIT_CONFIG = dict(
    verbosity=2
)

# get_var(<key>, <default_val>)
USE_STACK = get_var('stack_dir', 'images')


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

def task_build():
    """Build image stack for all plans"""
    return {
        'actions': [run_build],
        'file_dep': ['artifacts/IMAGES_CHANGED'],
        'targets': ['artifacts/builder-metainfo.json', 'artifacts/IMAGES_BUILT'],
        'params':[
            {
                'name': 'stack_dir',
                'short': 'd',
                'long': 'stack_dir',
                'default': 'images'
            },
            {
                'name': 'dry_run',
                'short': 's',
                'long': 'dry_run',
                'default': False
            },
        ],
    }


def task_test():
    """Test built images"""
    def quick_test():
        print(f'*** Testing ***')
        exit_code = pytest.main([
            '-x',       # exit instantly on first error or failed test
            '/home/runner/work/datahub-docker-stack/datahub-docker-stack/images/scipy-ml-notebook/test'  # test dirs
        ])
    return {
        'actions': [quick_test]
    }
    return {
        'actions': [run_test],
        'file_dep': ['artifacts/IMAGES_BUILT'],
        'targets': ['artifacts/IMAGES_TEST_PASSED', 'artifacts/IMAGES_TEST_ERROR'],
        'params':[
            {
                'name': 'stack_dir',
                'short': 'd',
                'long': 'stack_dir',
                'default': 'images'
            },
        ],
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
