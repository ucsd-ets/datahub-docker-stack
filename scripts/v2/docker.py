import docker
import logging
from scripts.v2.tree import Node
from typing import Tuple, List, Optional
import pandas as pd
from scripts.utils import strfdelta, bytes_to_hstring
from scripts.utils import strip_csv_from_md, csv_to_pd

logger = logging.getLogger(__name__)

__docker_client__ = docker.from_env()
__logged_in__ = False


class DockerError(Exception):
    pass


def set_docker_client(d: docker.DockerClient):
    __docker_client__ = d


def build(node: Node) -> bool:
    """Build a docker image from a node

    Args:
        node (Node): node to build
    """
    try:
        for line in __docker_client__.api.build(
            path=node.filepath,
            dockerfile=node.dockerfile,
            tag=node.image_name + ':' + node.image_tag,
            buildargs=node.build_args,
            nocache=True,
            rm=False
        ):

            print(line)
        return True
    except Exception as e:
        logger.error("couldnt build docker image; " + str(e))
        return False
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
    except docker.errors.APIError as e:
        raise DockerError(e)


def push(node: Node):
    try:
        # login to dockerhub
        # push

        stream = __docker_client__.images.push(
            node.image_name, node.image_tag, stream=True, decode=True)

        
        for chunk in stream:
            logger.info(chunk)

            if 'status' in chunk:
                # "The push refers to repository XXX_repo"
                if node.image_name in chunk['status']:
                    logger.info(chunk['status'])

                # "XXX_tag: digest: sha256:XXX size: XXX"
                elif node.image_tag in chunk['status']:
                    logger.info('\n' + chunk['status'])

                # regular progress
                else:
                    logger.info('.')
    except Exception as e:
        logger.error(e)

    finally:
        __docker_client__.close()

def report(node):

    def get_layers(image):
        df = pd.DataFrame(image.history()).convert_dtypes()
        df['CMD'] = df['CreatedBy']
        df['CMD'] = df['CMD'].str.replace('|', '', regex=False)
        df['CMD'] = df['CMD'].str.replace('/bin/bash -o pipefail -c', '', regex=False)
        df['CMD'] = df['CMD'].str.replace('#(nop)', '', regex=False)
        df['CMD'] = '`' + df['CMD'].str.strip() + '`'
        df['createdAt'] = pd.to_datetime(df['Created'], unit='s')
        df['hSize'] = df['Size'].apply(
            lambda x: bytes_to_hstring(x) if x > 100 else f'{x} B'
        )
        df['cumSize'] = df['Size'][::-1].cumsum()[::-1]
        df['hcumSize'] = df['cumSize'].apply(
            lambda x: bytes_to_hstring(x) if x > 100 else f'{x} B'
        )
        df_ordered = (
            df.loc[df['Tags'].notna()[::-1].cumsum()[::-1] > 0, :]
            .iloc[::-1, :]
            .reset_index(drop=True)
        )
        df_ordered['elapsed'] = df_ordered['createdAt'].diff()
        df_ordered.loc[1, 'elapsed'] = pd.Timedelta(0)
        df_ordered['elapsed'] = df_ordered['elapsed'].apply(strfdelta)
        return df_ordered
    

    __docker_client__.images.get(node.image_name + ':' + node.image_tag)