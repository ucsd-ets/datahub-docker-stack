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

from scripts.v2.wiki import update_Stable


import pytest
import requests


DOIT_CONFIG = dict(
    verbosity=2
)

# get_var(<key>, <default_val>)
USE_STACK = get_var('stack_dir', 'images')

# KEEP
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


# KEEP
def task_tag():
    """Tag and push images with new tags"""
    return {
        'actions': [run_tagging],
        'uptodate': [False],
        'file_dep': ['artifacts/.empty', 'logs/.empty'],
        'targets': ['artifacts/IMAGES_TAGGED'],
        'params':[ 
            {
                'name': 'original_tag',
                'long': 'original_tag',
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

# KEEP
# TODO: rewrite function
def task_stable():
    """Build image manifests for all stable tagged images"""
    return {
        'actions': [update_Stable]
    }
