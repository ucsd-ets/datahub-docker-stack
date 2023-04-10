# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from plumbum.cmd import git
from pathlib import PurePath
from os import path,environ
import json

from scripts.utils import store_var,get_specs

from scripts.utils import get_logger
logger = get_logger()

class GitHelper:
    @staticmethod
    def commit_hash() -> str:
        return git["rev-parse", "HEAD"]().strip()

    @staticmethod
    def commit_hash_tag() -> str:
        return GitHelper.commit_hash()

    @staticmethod
    def commit_hash_tag_shortened() -> str:
        return GitHelper.commit_hash()[:7]

    @staticmethod
    def commit_message() -> str:
        return git["log", -1, "--pretty=%B"]().strip()

    @staticmethod
    def commit_changed_files() -> list:
        print(environ['GITHUB_REF_NAME'])
        return git['diff', "HEAD^", "HEAD", '--name-only']().split()


def get_changed_images():
    changed_images = set()
    changed_files = GitHelper.commit_changed_files()
    # read all image name
    spec = get_specs('images/spec.yml')
    images = list(spec['images'].keys())
    # read all build tags
    with open('images/change_ignore.json','r') as ftp:
        tags = json.load(ftp)
    
    for file in changed_files:
        fp = PurePath(file)
        logger.info(f"Detecting changed file: {file}")
        # need to be under images and must be a folder
        if fp.parts[0] == 'images':
            image_ref = fp.parts[1]
            if image_ref in tags['BuildAll']:
                changed_images.update(images)
                # included all images so break and proceed as all images needs to be built
                break
            if image_ref not in changed_images and image_ref not in tags['ChangeIgnore']:
                logger.info(f"Changed file {file} belongs to {image_ref}. Will rebuild.")
                changed_images.add(image_ref)
    
    return list(changed_images)


def save_changed_images():
    """
    side-effects: 
    """
    images = get_changed_images()
    print('Images changed:', images)
    store_var('IMAGES_CHANGED', images)


def save_git_info():
    for fp, func in {
        'GIT_HASH': GitHelper.commit_hash_tag,
        'GIT_HASH_SHORT': GitHelper.commit_hash_tag_shortened,
        'GIT_MESSAGE': GitHelper.commit_message,
        'GIT_CHANGED_FILES': GitHelper.commit_changed_files
    }.items():
        store_var(fp, func())


if __name__ == "__main__":
    print("Git hash:", GitHelper.commit_hash())
    print("Git hash:", GitHelper.commit_hash_tag())
    print("Git hash shortened:", GitHelper.commit_hash_tag_shortened())
    print("Git message:", GitHelper.commit_message())
    print("Git changed files:", GitHelper.commit_changed_files())
    print('Git changed images', get_changed_images())
