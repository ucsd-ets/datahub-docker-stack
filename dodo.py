import os
pjoin = os.path.join
from shutil import rmtree

from scripts.git_helper import save_changed_images, save_git_info
from scripts.docker_builder import run_build
from scripts.docker_tester import run_test
from scripts.docker_pusher import run_push
from scripts.manifests import run_manifests


DOIT_CONFIG = dict(
    verbosity=2
)


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
        if os.path.exists('manifests'):
            rmtree('manifests')
    
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
    }


def task_test():
    """Test built images"""
    return {
        'actions': [run_test],
        'file_dep': ['artifacts/IMAGES_BUILT'],
        'targets': ['artifacts/IMAGES_TEST_PASSED', 'artifacts/IMAGES_TEST_ERROR'],
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
        'targets': ['manifests/*.md']
    }
