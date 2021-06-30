import itertools
import re
import os
from typing import NamedTuple; pjoin = os.path.join
import logging
import time
from collections import namedtuple
import json

import docker
from docker.utils.json_stream import json_stream
from docker.errors import BuildError

from scripts.utils import get_specs


logger = logging.getLogger(__name__)

LayerMeta = namedtuple(
    typename='LayerMeta',
    field_names=['CMD', 'START_T', 'FINISH_T', 'LOGS', 'ID']
)

def dbuild(
    path: str, image_tag: str, build_args=None, 
    docker_client=docker.from_env(), verbose=True, nocache=False
):
    """
    Adopted from https://github.com/docker/docker-py/blob/master/docker/models/images.py
    """
    try:
        logger.info(f"Begin build for {pjoin(path, 'Dockerfile')}")
        logger.info(
            f"dbuild(path={path}, image_tag={image_tag}, build_args={build_args}, "
            f"verbose={True}, nocache={nocache})"
        )

        resp = docker_client.api.build(
            path=path, dockerfile='Dockerfile', tag=image_tag,
            buildargs=build_args,
            nocache=nocache,
        )
        meta = []

        result_stream, internal_stream = itertools.tee(json_stream(resp))
        last_event = None
        image_id = None
        last_layer_cmd = None
        last_layer_start_time = None
        last_layer_finish_time = None
        last_layer_id = None
        last_layer_logs = []

        ptrn_step = r'^Step (\d+\/\d+) : (.+)'
        ptrn_layer = r'^ ---> ([a-z0-9]+)'
        ptrn_success = r'(^Successfully built |sha256:)([0-9a-f]+)$'

        for chunk in internal_stream:
            logger.info(chunk)

            if 'error' in chunk:
                raise BuildError(chunk['error'], result_stream)

            if 'stream' in chunk:
                if verbose:
                    print(chunk['stream'], end='')

                raw_output = chunk['stream']
                if (match_step := re.search(ptrn_step, raw_output)) is not None:
                    if last_layer_cmd:
                        meta.append(LayerMeta(
                            CMD=last_layer_cmd,
                            START_T=last_layer_start_time,
                            FINISH_T=last_layer_finish_time,
                            LOGS=last_layer_logs,
                            ID=last_layer_id,
                        ))
                        last_layer_cmd = None
                        last_layer_start_time = None
                        last_layer_finish_time = None
                        last_layer_id = None
                        last_layer_logs = []
                    last_layer_cmd = match_step.group(2)
                    last_layer_start_time = time.time()
                elif (match_layer := re.search(ptrn_layer, raw_output)) is not None:
                    last_layer_id = match_layer.group(1)
                    last_layer_finish_time = time.time()
                elif (match_success := re.search(ptrn_success, raw_output)) is not None:
                    meta.append(LayerMeta(
                        CMD=last_layer_cmd,
                        START_T=last_layer_start_time,
                        FINISH_T=last_layer_finish_time,
                        LOGS=last_layer_logs,
                        ID=last_layer_id,
                    ))
                    image_id = match_success.group(2)
                else:
                    last_layer_logs.append(raw_output)

            last_event = chunk

        if image_id:
            image = docker_client.images.get(image_id)
            logger.info(f"Successfully finish build for {image}")
            return image, meta

        raise BuildError(last_event or 'Unknown', result_stream)

    except BuildError as err:
        print('!!! Build failed !!!')
        # for l in err.build_log:
        #     if 'stream' in l:
        #         print(' ', l['stream'], end='')
        logger.error(f"Build failed when building {image_tag}: {err.msg}")
        raise err
    
    except KeyboardInterrupt:
        logger.error('Interrupted')
        raise KeyboardInterrupt(f'{image_tag}')


class DockerStackBuilder:
    """
    Check for errors
    for each build:
    - image (directory)
    - tag (git-hash)
    """
    def __init__(self, path, specs, plan, images_changed=[], dry_run=False):
        self.path = path
        self.specs_fp = specs
        self.specs = get_specs(pjoin(path, specs))
        self.plan = plan
        self.dry_run = dry_run
        # TODO: replace ordering here, use subtree
        self.images_order = [short_name for short_name in self.specs['images'].keys()]
        self.images = {}
        self.metas = {}

        # sanity check
        assert plan in self.specs['plans'].keys()
        self.images_dirs = []
        with os.scandir(path) as it:
            for entry in it:
                if not entry.is_file() and not entry.name.startswith('.'):
                    self.images_dirs.append(entry)
        assert len(self.specs['images']) == len(self.images_dirs)
        # TODO: maybe more checks
    
    def __enter__(self):
        logger.info(f"Building image stack from {self.path} using {self.specs_fp}")
        for short_name in self.images_order:
            # prep
            image_spec = self.specs['images'][short_name]
            path = pjoin(self.path, short_name)
            # FIXME: change to git-tag
            image_tag = f"{image_spec['image_name']}:{self.specs['plans'][self.plan]['tag_prefix']}-111111"
            image_spec['image_tag'] = image_tag
            build_args = {}

            # fill buildargs for `$BASE_TAG`
            if 'depend_on' in image_spec:
                base_full_tag = self.specs['images'][image_spec['depend_on']]['image_tag']
                custom_tag = base_full_tag.split(':')[1]
                build_args.update(BASE_TAG=custom_tag)
            
            # fill buildargs for extra vars defined in spec.yml
            if 'dbuild_env' in image_spec:
                dbuild_env = image_spec['dbuild_env']
                if 'common' in dbuild_env.keys():
                    build_args.update(dbuild_env['common'])
                if self.plan in dbuild_env.keys():
                    build_args.update(dbuild_env[self.plan])
            
            if not self.dry_run:
                # Go to build
                logger.info('') # TODO: fill meta info
                image, meta = dbuild(
                    path=path,
                    build_args=build_args,
                    image_tag=image_tag,
                    nocache=True
                )
                self.images[short_name] = image
                self.metas[short_name] = meta
    
    def __exit__(self, exc_type, exc_value, traceback):
        with open(pjoin(self.path, 'builder-metainfo.json'), 'w') as f:
            json.dump(self.metas, f)

if __name__ == '__main__':
    # docker_client=docker.from_env()
    # image = dbuild(
    #     path='images\datahub-base-notebook',
    #     build_args={'PYTHON_VERSION': 'python-3.8.8'},
    #     image_tag='base:test',
    #     docker_client=docker_client
    # )
    # print(image)


    logging.basicConfig(filename='builder.log', level=logging.INFO)
    builder = DockerStackBuilder(path='images', specs='spec.yml', plan='PYTHON38')
    builder.__enter__()
    builder.__exit__(None, None, None)
