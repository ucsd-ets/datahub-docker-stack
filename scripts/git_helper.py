# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from plumbum.cmd import git
from pathlib import PurePath
from os import path

from scripts.utils import store_var


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
        return git['diff', 'origin/main', '--name-only']().split()


def get_changed_images():
    changed_images = set()
    changed_files = GitHelper.commit_changed_files()
    
    for file in changed_files:
        fp = PurePath(file)
        # need to be under images and must be a folder
        if fp.parts[0] == 'images':
            image_ref = fp.parts[1]
            if image_ref not in changed_images:
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
