import docker
from typing import List
import os
import logging
import argparse
import sys

from scripts.docker_pusher import push_images, docker_login
from scripts.v2.utils import get_logger, read_history, query_images, read_var, store_var
from scripts.v2 import docker_adapter

logger = get_logger()


def run_tagging(
        original_tag, 
        username: str,
        password: str,
        dry_run=False) -> bool:
    """runner of tag images github workflow.

    Args:
        original_tag (_type_): by user input in workflow, sth like '2023.2-deadbeef'
        username (str): docker username, passed in as env variable
        password (str): docker token, passed in as env variable
        dry_run (bool, optional): True if we just want to check which images will be tagged. 
            Defaults to True.

    Returns:
        bool: success or failure
    """

    docker_adapter.login(username, password)
    
    assert original_tag and original_tag.count('-') == 1, \
        "None as input or incorrect tag format (should be like '2023.2-deadbeef')"
     
    ## count('-') == 1 -> split list must have length 2
    tag_prefix, short_hash = original_tag.rsplit('-', 1) 
    stable_tag = tag_prefix + '-stable'

    # will only read image info from Home.md
    history = read_history()
    original_names = query_images(history, short_hash, tag_prefix)  # a list

    if dry_run:
        logger.info(f"Doing dry-run to check original_names: {original_names}")
        tagged = [name.split(':')[0] + ':' + stable_tag for name in original_names]
        store_var('IMAGES_TAGGED', tagged )
        store_var('IMAGES_ORIGINAL', original_names )
        logger.info("DRY_RUN: original images written to IMAGES_ORIGINAL, stable images to IMAGES_TAGGED.")
        return True

    logger.info("prepulling images")
    docker_adapter.prepull_images(orig_images=original_names)
    logger.info("finished prepull")

    tagged = [] # each element is like 'ucsdets/datahub-base-notebook:2023.2-stable'
    for img_orig in original_names:
        logger.info(f'Tagging {img_orig} with {stable_tag}')
        img_stable, success = docker_adapter.tag_stable(orig_fullname=img_orig, tag_replace=stable_tag)
        if not success:
            logger.error(f"{img_orig} fails the tagging.")
            return False
        tagged.append(img_stable)
        

    store_var('IMAGES_TAGGED', tagged )
    store_var('IMAGES_ORIGINAL', original_names )
    logger.info("original images written to IMAGES_ORIGINAL, stable images to IMAGES_TAGGED.")
    
    logger.info("Pushing all stable images to Dockerhub.")
    return docker_adapter.push_stable_images(stable_fullnames=tagged)


def tagging_main(original_tag, dry_run=False):
    os.environ['GITHUB_REF_NAME'] = 'refractor_buildtest'
    dockerhub_username = os.environ.get('DOCKERHUB_USER', None)
    dockerhub_token = os.environ.get('DOCKERHUB_TOKEN', None)
    if not dockerhub_username or not dockerhub_token:
        logger.error('dockerhub username or password not set')
        sys.exit(1)
    
    tagging_result = run_tagging(
        original_tag, 
        username=dockerhub_username, 
        password=dockerhub_token,
        dry_run=dry_run
    )
    if tagging_result is False:
        logger.error("There was a problem while tagging images. Please consult logs.")
        sys.exit(5)
