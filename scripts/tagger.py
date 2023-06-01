import docker
from typing import List
import os
import logging
import argparse
import sys

from scripts.utils import get_logger, read_history, query_images, read_var, store_var, get_specs
from scripts import docker_adapter

logger = get_logger()


def run_tagging(
        original_tag: str, 
        username: str,
        password: str,
        dry_run=False) -> bool:
    """Fetch images like ucsdets/datascience-notebook:2023.2-<branch_name> and tag them into
    ucsdets/datascience-notebook:2023.2-stable.

    Args:
        original_tag (str): by user input in workflow, sth like '2023.2-<branch_name>'
        username (str): docker username, passed in as env variable
        password (str): docker token, passed in as env variable
        dry_run (bool, optional): True if we just want to check which images will be tagged. 
            Defaults to True.

    Returns:
        bool: success or failure
    """

    docker_adapter.login(username, password)
    
    # <branch_name> may contain more '-', but there must be one before it.
    assert original_tag and original_tag.count('-') >= 1, \
        "None as input or incorrect tag format (should be like '2023.2-<branch_name>')"
     
    # split only once from left -> 2 parts
    tag_prefix, branch_name = original_tag.split('-', 1) 
    branch_name = branch_name.replace("/", "_")
    stable_tag = tag_prefix + '-stable'

    # Get image names from spec.yml
    _spec = get_specs('images/spec.yml')  # a dictionary
    # a list of 'datascience-notebook'
    _images = list(_spec['images'].keys())
    original_names = ['ucsdets/' + name + original_tag for name in _images]

    if dry_run:
        logger.info(f"Doing dry-run to check original_names: {original_names}")
        tagged = [name.split(':')[0] + ':' + stable_tag for name in original_names]
        store_var('IMAGES_TAGGED', tagged )
        store_var('IMAGES_ORIGINAL', original_names )
        logger.info("DRY_RUN: original images written to IMAGES_ORIGINAL, stable images to IMAGES_TAGGED.")
        return True

    logger.info("prepulling images")
    docker_adapter.prepull_tagging_images(orig_images=original_names)
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


def run_global_stable_tagging(
        stablePrefix: str, 
        username: str,
        password: str,
        dry_run=False) -> bool:
    """Fetch images like ucsdets/datascience-notebook:2023.2-stable and tag them into
    ucsdets/datascience-notebook:stable

    Args:
        stablePrefix (str): by user input in workflow, sth like '2023.2'
        username (str): docker username, passed in as env variable
        password (str): docker token, passed in as env variable
        dry_run (bool, optional): True if we just want to check which images will be tagged. 
            Defaults to True.

    Note:
        Here, we only allow images with <year_quater-stable> tag, which we will call 'original_stable',
        like '2023.2-stable', to be tagged global_stable, 'stable'.

    Returns:
        bool: success or failure
    """

    docker_adapter.login(username, password)
    
    # sanity check on '2099.3'
    assert stablePrefix and len(stablePrefix) == 6 and stablePrefix.count('.') == 1, \
        "stablePrefix should be in the form of '2022.2'"

    # will only read original_stable image info from Home.md
    try:
        history = read_history()
        original_stable_names = query_images(history, 'stable', stablePrefix)  # a list
    except Exception as e:
        logger.error(f"Error when reading original stable image information, {e}")
        return False

    if dry_run:
        logger.info(f"Doing dry-run to check original_stable_names: {original_stable_names}")
        tagged = [name.split(':')[0] + ':' + 'stable' for name in original_stable_names]
        store_var('IMAGES_GLOBAL_STABLE', tagged )
        store_var('IMAGES_ORIGINAL_STABLE', original_stable_names )
        logger.info("DRY_RUN: original_stable images written to IMAGES_ORIGINAL_STABLE, global_stable images to IMAGES_GLOBAL_STABLE.")
        return True

    logger.info("prepulling original stable images")
    docker_adapter.prepull_tagging_images(orig_images=original_stable_names)
    logger.info("finished prepull")

    tagged = [] # each element is like 'ucsdets/datahub-base-notebook:stable'
    for img_orig in original_stable_names:
        logger.info(f"Tagging {img_orig} with 'stable'")
        img_stable, success = docker_adapter.tag_stable(orig_fullname=img_orig, tag_replace='stable')
        if not success:
            logger.error(f"{img_orig} fails the global_stable tagging.")
            return False
        tagged.append(img_stable)
        

    store_var('IMAGES_TAGGED', tagged )
    store_var('IMAGES_ORIGINAL', original_stable_names )
    logger.info("original_stable images written to IMAGES_ORIGINAL, global_stable images to IMAGES_TAGGED.")
    
    logger.info("Pushing all global_stable images to Dockerhub.")
    return docker_adapter.push_stable_images(stable_fullnames=tagged)


def tagging_main(original_tag, dry_run=False, global_stable=False):
    dockerhub_username = os.environ.get('DOCKERHUB_USER', None)
    dockerhub_token = os.environ.get('DOCKERHUB_TOKEN', None)
    if not dockerhub_username or not dockerhub_token:
        logger.error('dockerhub username or password not set')
        sys.exit(1)
    
    tagging_main_result = False
    if global_stable:
        tagging_result = run_global_stable_tagging(
            original_tag, 
            username=dockerhub_username, 
            password=dockerhub_token,
            dry_run=dry_run
        )
    else:
        tagging_result = run_tagging(
            original_tag, 
            username=dockerhub_username, 
            password=dockerhub_token,
            dry_run=dry_run
        )
    if tagging_result is False:
        logger.error("There was a problem while tagging images. Please consult logs.")
        sys.exit(5)
