import os
pjoin = os.path.join
from shutil import rmtree
from doit import get_var
import pytest
import requests

from scripts.tagger import tagging_main
from scripts.wiki import update_Stable


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


def task_tag():
    """Tag and push images with new tags"""
    return {
        'actions': [tagging_main],
        'uptodate': [False],
        'file_dep': ['artifacts/.empty', 'logs/.empty'],
        'targets': ['artifacts/IMAGES_TAGGED'],
        'params':[ 
            {
                'name': 'original_tag',
                'long': 'original_tag',
                'type': str,
                'default': None
            },
            {
                'name': 'dry_run',
                'short': 's',
                'long': 'dry_run',
                'type': bool,
                'default': False
            },
        ],
    }

def task_stable():
    """Build image manifests for all stable tagged images"""
    return {
        'actions': [update_Stable]
    }
