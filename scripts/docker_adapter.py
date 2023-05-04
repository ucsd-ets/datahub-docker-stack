import docker as docker_client
import logging
import json
from typing import Tuple, Optional, List
import pandas as pd

from scripts.tree import Node
from scripts.utils import get_logger, store_var
import os
import datetime


logger = get_logger()

# this should be set to >= docker client timeout, otherwise strange error.
os.environ['COMPOSE_HTTP_TIMEOUT'] = '300'
# prune funcs may timeout, see https://github.com/docker/compose/issues/3927
# os.environ['DOCKER_CLIENT_TIMEOUT'] = '300'     # this doesn't work
# solution: increase timeout in constructor directly.
__docker_client = docker_client.from_env(timeout=300)


class DockerError(Exception):
    pass


def set_docker_client(d: docker_client.DockerClient):
    global __docker_client
    __docker_client = d


def build(node: Node) -> Tuple[bool, str]:
    """Build a docker image from a node
    Use build() from docker.client.images (high-level) instead of low-level API

    Throws:
        see https://docker-py.readthedocs.io/en/stable/images.html

    Args:
        node (Node): node to build
    """
    logger.info(f"Build {node.image_name} now with buildargs = {node.build_args}")
    
    try:
        report = ''
        logger.debug(f'Build')
        """ img_obj, generator = __docker_client.images.build(
            path=node.filepath,
            dockerfile=node.dockerfile,
            tag=node.image_name + ':' + node.image_tag,
            buildargs=node.build_args,
            nocache=True,
            rm=False
        ) """
        # BUG NOTE: The following unpacking of generator must be included.
        # Otherwise the function will return before `docker build` completes,
        # causing unknown behavior.
        start_t = datetime.datetime.now()
        for line in __docker_client.api.build(
            path=node.filepath,
            dockerfile=node.dockerfile,
            tag=node.image_name + ':' + node.image_tag,
            buildargs=node.build_args,
            nocache=True,
            rm=False
        ):
            # line is of type dict
            content_str = line.get('stream', '').strip()    # sth like 'Step 1/20 : ARG PYTHON_VERSION=python-3.9.5'
            if content_str:     # if not empty string
                # time each major step (Step 1/23 : xxx)
                if content_str[:4] == "Step":
                    duration = datetime.datetime.now() - start_t
                    seconds = duration.total_seconds()
                    minutes = int(seconds // 60)
                    seconds = int(seconds % 60)
                    report += f'[{minutes}min {seconds}s] '
                    start_t = datetime.datetime.now()
                    # logger.info(f"{content_str}")
                    # for key, value in line.items():
                    #     logger.info(f"key: {key}, value: {value}")
                report += content_str + '\n'
        logger.info(f"Now we have these images: { __docker_client.images.list()}")

        return True, report

    except docker_client.errors.BuildError as build_e:
        logger.error(f"Error during build of {node.image_name},\n {build_e}")
        return False, report
    except docker_client.errors.APIError as api_e:
        logger.error(f"Server returns error during build of {node.image_name},\n {api_e}")
        return False, report
    except Exception as e:
        logger.error("Unrecognized error; \n" + str(e))
        return False, report
    
    finally:
        __docker_client.close()


def login(
    username: str, password: str,
    registry: Optional[str] = 'https://index.docker.io/v1/'
):
    """
    Log in to a docker registry given username, password and registry (optional)
    """
    try:
        logger.info(f'Logging into registry {registry} as {username}')
        r = __docker_client.login(username, password, registry=registry)
        if 'Status' in r.keys() and 'succeeded' in r['Status'].lower():
            return True
        raise ValueError(
            f'Username/password incorrect for registry {registry}')
    except docker_client.errors.APIError as e:
        raise DockerError(e)


def push(node: Node) -> Tuple[bool, str]:

    try:
        # login to dockerhub
        # push

        stream = __docker_client.images.push(
            node.image_name, node.image_tag, stream=True, decode=True)

        res = ""
        for chunk in stream:
            # logger.info(chunk)

            if 'status' in chunk:
                # "The push refers to repository XXX_repo"
                if node.image_name in chunk['status']:
                    res += chunk['status']
                    logger.info(chunk['status'])

                # "XXX_tag: digest: sha256:XXX size: XXX"
                elif node.image_tag in chunk['status']:
                    formatted_log = '\n' + chunk['status']
                    res += formatted_log
                    logger.info(formatted_log)

                # regular progress; skip
                else:
                    continue

        return True, res
    except Exception as e:
        logger.error(e)
        return False, res

    finally:
        __docker_client.close()


def get_image_obj(node: Node) -> docker_client.models.images.Image:
    # check (if str in List) before get image object
    try:
        return __docker_client.images.get(node.full_image_name)
    except docker_client.errors.ImageNotFound:
        logger.error(f"{node.full_image_name} not inside the \
                docker env {__docker_client.images.list()}.")
        return None


def run_simple_command(container: docker_client.models.containers.Container,
        node: Node, cmd: str) -> Tuple[str, bool]:
    """Given a docker container, run a command, return the output, and remove the container.

    Args:
        container: the detached container created by run(tty=True)
        node (Node): _description_
        cmd (str): terminal command to exec, e.g. "conda list"

    Returns:
        str: terminal output decoded as string
        bool: success/faliure
    """
    # Run command
    logger.info(f"Running cmd: '{cmd}' on container: {container}")
    try:
        out = container.exec_run(cmd)
        assert out.exit_code == 0, f"Command: {cmd} failed"
        result_str = out.output.decode("utf-8").rstrip()
        logger.debug(f"Command result: {result_str}")

        return result_str, True
    except Exception as e:
        logger.error(e)
        print(
            f"*** docker container on image {node.image_name} failed to exec cmd {cmd} ***")
        return "Failed to execute cmd", False


def list_images():
    try:
        return __docker_client.images.list()
    except Exception as e:
        logger.error(f'couldnt list images; {e}')
    finally:
        __docker_client.close()


def prune(full_image_name: str) -> int:
    """clear build & test cache, reclaim space

    Args:
        full_image_name (str): sth like ucsdets/datahub-base-notebook:2023.2-deadbeef

    Returns:
        int: space reclaimed in number of bytes.
    """
    try:
        __docker_client.images.remove(image=full_image_name, force=True)
    except Exception as e:
        logger.error(f"couldn't remove image {full_image_name}; {e}")
        logger.error("Forcing system prune docker prune -af")
        os.system('docker system prune -af')
        return 0

    prune_funcs = [
        ('containers.prune', __docker_client.containers.prune),
        ('images.prune', __docker_client.images.prune),
        ('volumes.prune', __docker_client.volumes.prune)
    ]
    total_space_reclaimed = 0

    try:
        for func_name, prune in prune_funcs:
            resp = prune()
            logger.debug(f"from prune function {func_name}, resp is {resp}")
            if not 'SpaceReclaimed' in resp:
                logger.error(
                    f'SpaceReclaimed not in API response for prune function {func_name}. \
                    keys = {resp.keys()}'
                )
                continue
            total_space_reclaimed += resp.pop('SpaceReclaimed')
        return total_space_reclaimed

    except Exception as e:
        logger.error(f"couldn't prune docker; {e}")
        logger.error("Forcing system prune docker prune -af")
        os.system('docker system prune -af')
        return 0
    finally:
        __docker_client.close()


def prepull_images(orig_images: List[str]) -> bool:
    """pull down all the images to docker in order to tag later

    Args:
        orig_images (List[str]): each is like 'ucsdets/datahub-base-notebook:2023.2-deadbeef'

    Returns:
        bool: success or failure
    """
    currImage = "placeholder"
    try:
        for full_name in orig_images:
            currImage = full_name
            # logger.info(f'Tagging action: Pulling original image {full_name}')
            assert full_name.count(':') == 1, f"{full_name} should have exactly one :"
            img, tag = full_name.split(':')
            img = img.lstrip()
            tag = tag.rstrip()
            __docker_client.images.pull(img, tag)

        return True
    except Exception as e:
        logger.error(f"Tagging action: Fail to pull {currImage}")
        return False
    finally:
        __docker_client.close()


def tag_stable(orig_fullname: str, tag_replace: str) -> Tuple[str, bool]:
    """guarding wrapper around actual docker.image.tag()

    Args:
        orig_fullname (str): of format 'ucsdets/datahub-base-notebook:2023.2-deadbeef'
        tag_replace (str): of format '2023.2-stable'

    Returns:
        str: 'ucsdets/datahub-base-notebook:2023.2-stable' or empty string if failed
        bool: success or failure
    """
    try:
        img_obj = __docker_client.images.get(orig_fullname)
        assert orig_fullname.count(':') == 1, f"{orig_fullname} should have exactly one :"
        repo, _ = orig_fullname.split(':')
        img_obj.tag(repository=repo, tag=tag_replace)
        return repo + ':' + tag_replace, True
    except Exception as e:
        logger.error(f"Error when tagging image {orig_fullname}, \n{e}")
        return '', False 
    finally:
        __docker_client.close()

def push_stable_images(stable_fullnames: List[str]) -> bool:
    """given a list of stable image names, push them to dockerhub.
    If success, these strings will be written to IMAGES_PUSHED in build-artifacts

    Args:
        stable_fullnames (List[str]): each is like 'ucsdets/datahub-base-notebook:2023.2-stable'

    Returns:
        bool: success or failure
    """
    images_pushed = []
    for stable_name in stable_fullnames:
        try:
            # get image obj
            stable_obj = __docker_client.images.get(stable_name)
        except docker_client.errors.ImageNotFound:
            logger.error(f"{stable_name} not inside the \
                docker env {__docker_client.images.list()}")
            break
        except Exception as e:
            logger.error(f"Something wrong with the server when get() {stable_name}")
            break

        try:
            # push tagged image
            repo, tag = stable_name.split(':')
            resp = __docker_client.images.push(
                repo, tag,
                stream=True,
                decode=True
            )   # this will return a geneator of json-decoded dict

            # can check push log here if anything goes wrong
            for chunk in resp:
                """ 
                NOTE: resp is a generator
                We MUST go thru resp to ensure docker push is finished.
                To show log (defined below), comment out 'continue'
                """
                continue

                if 'status' in chunk:
                    # "The push refers to repository XXX_repo"
                    if repo in chunk['status']:
                        print(chunk['status'])

                    # "XXX_tag: digest: sha256:XXX size: XXX"
                    elif tag in chunk['status']:
                        print('\n' + chunk['status'])

                    # regular progress
                    else:
                        # print('.', end='')
                        print("****** ", chunk['status'])
                        
        except Exception as e:
            logger.error(f"Something wrong with the server when push() {stable_name}")
            break
        images_pushed.append(stable_name)
    # finally:
    __docker_client.close()

    if len(stable_fullnames) != len(images_pushed):
        return False
    else:
        store_var('IMAGES_PUSHED', images_pushed)
        return True
