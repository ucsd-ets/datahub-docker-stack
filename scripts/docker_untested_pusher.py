import docker
import logging
import os

from scripts.utils import read_var, store_var

from typing import Tuple, List, Optional
ImageFulltagPair = Tuple[docker.models.images.Image, str]

logger = logging.getLogger(__name__)


def docker_login(
    client: docker.DockerClient, username: str, password: str,
    registry: Optional[str] = 'https://index.docker.io/v1/'
):
    """
    Log in to a docker registry given username, password and registry (optional)
    """
    logger.info(f'Logging into registry {registry} as {username}')
    r = client.login(username, password, registry=registry)
    if 'Status' in r.keys() and 'succeeded' in r['Status'].lower():
        return True
    raise ValueError(f'Username/password incorrect for registry {registry}')


def push_images(
    client: docker.DockerClient, pairs: List[ImageFulltagPair], externally_tested_images = ['ucsdets/scipy-ml-notebook']
):
    """
    Push a list of images with untested tag if they are externally tested
    """
    images_pushed = []
    for image, full_tag in pairs:
        print(f"inside push {image}")
        logger.info(f'Attempting to push {image}')

        if ':' not in full_tag:
            repository = full_tag
            tag = 'latest'
        else:
            repository,tag = full_tag.split(':')
        
        tag = tag + '-untested'
        if repository not in externally_tested_images:
            print(f"skipping {repository}")
            continue

        try:
            print("inside push")
            logger.info(f'Attempting to push {image} to {repository}:{tag}')

            image.tag(repository,tag)

            r = client.images.push(
                repository, tag,
                stream=True,
                decode=True,
            )

            for chunk in r:
                print("chuck is", chunk)
                logger.info(chunk)

                if 'status' in chunk:
                    # "The push refers to repository XXX_repo"
                    if repository in chunk['status']:
                        print(chunk['status'])

                    # "XXX_tag: digest: sha256:XXX size: XXX"
                    elif tag in chunk['status']:
                        print('\n' + chunk['status'])

                    # regular progress
                    else:
                        print('.', end='')

            # push success
            images_pushed.append(full_tag)
            store_var('IMAGES_UNTESTED_PUSHED', images_pushed)
            print(f'pushed {image} to {repository}:{tag}')

        except docker.errors.APIError as e:
            logger.error('Untested images push error')
            raise e


def run_untested_push():
    cli = docker.from_env()
    if docker_login(cli, 'etsjenkins', os.environ['DOCKERHUB_TOKEN']):
        tags = read_var('IMAGES_BUILT')
        pairs = [
            (cli.images.get(tag), tag)
            for tag in tags
        ]
        push_images(cli, pairs)
