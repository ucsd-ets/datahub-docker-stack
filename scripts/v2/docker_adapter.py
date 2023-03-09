import docker as docker_client
import logging
import json
from typing import Tuple, Optional
import pandas as pd

from scripts.v2.tree import Node
from scripts.v2.utils import get_logger
import os


logger = get_logger()

__docker_client = docker_client.from_env()

class DockerError(Exception):
    pass


def set_docker_client(d: docker_client.DockerClient):
    global __docker_client
    __docker_client = d


def build(node: Node) -> Tuple[bool, str]:
    """Build a docker image from a node

    Args:
        node (Node): node to build
    """
    logger.info(f"Build {node.image_name} now")
    print("Now we have these images: ", __docker_client.images.list())
    try:
        report = ''
        for line in __docker_client.api.build(
            path=node.filepath,
            dockerfile=node.dockerfile,
            tag=node.image_name + ':' + node.image_tag,
            buildargs=node.build_args,
            nocache=True,
            rm=False
        ):
            raw_lines = line.decode('utf-8').split('\n')
            raw_lines = [line.rstrip() for line in raw_lines]
            
            for raw_line in raw_lines:
                try:
                    line_data = json.loads(raw_line, strict=False)
                    actual_line = line_data['stream']
                    if actual_line == '\n':
                        continue
                    # print(line_data['stream'])
                    report += line_data['stream']
                    logger.debug(f"{node.image_name}:{line_data['stream']}")
                except:
                    pass
        return True, report
    except Exception as e:
        logger.error("couldnt build docker image; " + str(e))
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
        raise ValueError(f'Username/password incorrect for registry {registry}')
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
            logger.info(chunk)

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

                # regular progress
                else:
                    logger.info('.')
        
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


def run_simple_command(node: Node, cmd: str) -> Tuple[str, bool]:
    """Create a docker container, run a command, return the output, and remove the container.

    Args:
        node (Node): _description_
        cmd (str): terminal command to exec, e.g. "conda list"

    Returns:
        str: terminal output decoded as string
        bool: success/faliure
    """
    # Create docker container
    logger.info(f"Creating container for image {node.full_image_name} ...")
    logger.info(f"Following images exist: {__docker_client.images.list()}")
    try:
        container = __docker_client.containers.run(
            image=node.image_name, command=cmd, detach=True,
        )   # If detach is True, a Container object is returned instead. 
    except Exception as e:
        logger.error(e)
        print(f"*** docker container failed to run on image {node.image_name} ***")
        return "Failed to create container", False
    
    logger.info(f"Container {container.name} created")

    # Run command
    logger.info(f"Running cmd: '{cmd}' on container: {container}")
    try:
        out = container.exec_run(cmd)
        assert out.exit_code == 0, f"Command: {cmd} failed"
    except Exception as e:
        logger.error(e)
        print(f"*** docker container on image {node.image_name} failed to exec cmd {cmd} ***")
        return "Failed to execute cmd", False
    finally:
        if container:
            container.remove(force=True)
        __docker_client.close()

    result_str = out.output.decode("utf-8").rstrip()
    logger.info(f"Command result: {result_str}")

    # Remove container
    if container:
        logger.info(f"Removing container {container.name} ...")
        container.remove(force=True)
        logger.info(f"Container {container.name} removed")

    return result_str, True

def prune(full_image_name: str) -> int:
    try:
        __docker_client.images.remove(image=full_image_name, force=True)
        prune_funcs = [
            ('images.prune', __docker_client.images.prune),
            ('networks.prune', __docker_client.networks.prune),
            ('volumes.prune', __docker_client.volumes.prune)
        ]
        total_space_reclaimed = 0

        # prune funcs may timeout, see https://github.com/docker/compose/issues/3927
        os.environ['DOCKER_CLIENT_TIMEOUT'] = '300'
        os.environ['COMPOSE_HTTP_TIMEOUT'] = '300'

        for func_name, prune in prune_funcs:
            
            resp = prune()
            if not 'SpaceReclaimed' in resp:
                logger.warning(f'SpaceReclaimed not in API response for prune function {func_name}. keys = {resp.keys()}')
                continue
            total_space_reclaimed += resp.pop('SpaceReclaimed')

        return total_space_reclaimed
    except Exception as e:
        logger.error(f"couldn't prune docker; {e}")
        return 0
    finally:
        __docker_client.close()
