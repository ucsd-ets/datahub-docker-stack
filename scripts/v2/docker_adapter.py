import docker as docker_client
import logging
from scripts.v2.tree import Node
from typing import Tuple, Optional
import pandas as pd
from scripts.utils import strfdelta, bytes_to_hstring
from scripts.utils import strip_csv_from_md, csv_to_pd

logger = logging.getLogger('datahub_docker_stacks')

__docker_client__ = docker_client.from_env()
__logged_in__ = False


class DockerError(Exception):
    pass


def set_docker_client(d: docker_client.DockerClient):
    __docker_client__ = d


def build(node: Node) -> Tuple[bool, str]:
    """Build a docker image from a node

    Args:
        node (Node): node to build
    """
    try:
        report = ''
        for line in __docker_client__.api.build(
            path=node.filepath,
            dockerfile=node.dockerfile,
            tag=node.image_name + ':' + node.image_tag,
            buildargs=node.build_args,
            nocache=True,
            rm=False
        ):
            as_str = line.decode('utf-8').rstrip()
            report += as_str
            logger.info(as_str)
        return True, report
    except Exception as e:
        logger.error("couldnt build docker image; " + str(e))
        return False, report
    finally:
        __docker_client__.close()


def login(
    username: str, password: str,
    registry: Optional[str] = 'https://index.docker.io/v1/'
):
    """
    Log in to a docker registry given username, password and registry (optional)
    """
    try:
        logger.info(f'Logging into registry {registry} as {username}')
        r = __docker_client__.login(username, password, registry=registry)
        if 'Status' in r.keys() and 'succeeded' in r['Status'].lower():
            __logged_in__ = True
            return __logged_in__
        raise ValueError(f'Username/password incorrect for registry {registry}')
    except docker_client.errors.APIError as e:
        raise DockerError(e)


def push(node: Node) -> Tuple[bool, str]:

    try:
        # login to dockerhub
        # push

        stream = __docker_client__.images.push(
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
        __docker_client__.close()


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
    logger.info(f"Creating container for image {node.image_name} ...")
    try:
        container = __docker_client__.containers.run(
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
        __docker_client__.close()

    result_str = out.output.decode("utf-8").rstrip()
    logger.info(f"Command result: {result_str}")

    # Remove container
    if container:
        logger.info(f"Removing container {container.name} ...")
        container.remove(force=True)
        logger.info(f"Container {container.name} removed")

    return result_str, True


