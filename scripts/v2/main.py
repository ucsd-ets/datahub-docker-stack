from scripts.v2 import git_helper
from scripts.v2.tree import build_tree, load_spec
from scripts.v2.runner import build_and_test_containers
from scripts.v2.utils import get_logger
import os
import logging
import argparse


def main(dockerhub_username: str, dockerhub_password: str):
    spec = load_spec()
    all_info_cmds = spec['all_info_cmds']
    tag_prefix = spec['tag']['prefix']

    images_changed = git_helper.get_changed_images()
    git_hash = git_helper.GitHelper.commit_hash_tag_shortened()

    root = build_tree(
        spec_yaml=spec, images_changed=images_changed, git_suffix=git_hash)

    build_and_test_containers(root=root,
                              username=dockerhub_username,
                              password=dockerhub_password,
                              tag_prefix=tag_prefix,
                              all_info_cmds=all_info_cmds)


# https://docs.python.org/3/library/logging.html#logging-levels
LOGLEVEL_MAP = {
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'DEBUG': logging.DEBUG,
    'CRITICAL': logging.CRITICAL,
    'NOTSET': logging.NOTSET,
    'ERROR': logging.ERROR
}

parser = argparse.ArgumentParser(
    prog='datahub_docker_stacks',
    description='Build, push, and test UCSD standard Data Science & Machine Learning Docker iamges'
)

parser.add_argument('-l', '--log-level', choices=list(LOGLEVEL_MAP.keys()), type=str, default='DEBUG')

if __name__ == '__main__':
    parsed_args = parser.parse_args()
    logger = get_logger(LOGLEVEL_MAP[parsed_args.log_level])

    # this variable will automatically be set by github
    os.environ['GITHUB_REF_NAME'] = 'refractor_buildtest'
    dockerhub_username = os.environ.get('DOKCERHUB_USER', None)
    dockerhub_token = os.environ.get('DOCKERHUB_TOKEN', None)
    if not dockerhub_username or not dockerhub_token:
        logger.error('dockerhub username or password not set')
        exit(1)

    main(dockerhub_username=dockerhub_username,
         dockerhub_password=dockerhub_token)
