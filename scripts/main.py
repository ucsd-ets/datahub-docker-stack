from scripts import git_helper
from scripts.tree import build_tree, load_spec
from scripts.runner import build_and_test_containers
from scripts.utils import get_logger
from scripts import git_helper
from scripts.tree import build_tree, load_spec
from scripts.runner import build_and_test_containers
from scripts.utils import get_logger
import os
import logging
import argparse
import sys


def main(dockerhub_username: str, dockerhub_password: str):
    spec = load_spec()
    all_info_cmds = spec['all_info_cmds']
    tag_prefix = spec['tag']['prefix']

    images_changed = git_helper.get_changed_images()
    
    # git_hash = git_helper.GitHelper.commit_hash_tag_shortened()
    # code for if/when we decide to change tags to branch names instead of hash refs.
    git_hash = git_helper.GitHelper.get_branch_name().replace("/", "-")

    if(git_hash == "stable"):
        logger.error("Please don't name your branch name stable.")
        sys.exit(5)

    root = build_tree(
        spec_yaml=spec, images_changed=images_changed, git_suffix=git_hash)

    build_result = build_and_test_containers(root=root,
                              username=dockerhub_username,
                              password=dockerhub_password,
                              tag_prefix=tag_prefix,
                              all_info_cmds=all_info_cmds)
    
    if build_result is False:
        sys.exit("There was a problem while building one of the images. Please consult logs.")


# https://docs.python.org/3/library/logging.html#logging-levels
LOGLEVEL_MAP = {
    # from top to bottom: 10, 20, 30, 40, 50, 0
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
    'NOTSET': logging.NOTSET
}

parser = argparse.ArgumentParser(
    prog='datahub_docker_stacks',
    description='Build, push, and test UCSD standard Data Science & Machine Learning Docker images'
)

parser.add_argument('-l', '--log-level', choices=list(LOGLEVEL_MAP.keys()), type=str, default='DEBUG')

if __name__ == '__main__':
    parsed_args = parser.parse_args()
    # logger = get_logger(LOGLEVEL_MAP[parsed_args.log_level])

    dockerhub_username = os.environ.get('DOCKERHUB_USER', None)
    dockerhub_token = os.environ.get('DOCKERHUB_TOKEN', None)
    if not dockerhub_username or not dockerhub_token:
        sys.exit("'dockerhub username or password not set'")

    main(dockerhub_username=dockerhub_username,
         dockerhub_password=dockerhub_token)
