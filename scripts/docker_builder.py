from scripts.utils import get_specs, read_var, store_dict, store_var
from scripts.docker_info import get_dependency
from scripts.utils import get_specs, read_var, store_dict, store_var, read_dict
from scripts.git_helper import get_changed_images
from docker.errors import BuildError
from docker.utils.json_stream import json_stream
from model.spec import BuilderSpec
import docker
from collections import namedtuple
import time
import logging
import itertools
import re
import os
from typing import NamedTuple
pjoin = os.path.join


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
                        )._asdict())
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
                    )._asdict())
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

    def __init__(self, path, specs, git_suffix, images_changed=[], dry_run=False):
        self.path = path
        self.specs_fp = specs
        self.specs = get_specs(pjoin(path, specs))
        self.git_suffix = git_suffix
        self.dry_run = dry_run
        self.images_changed = images_changed
        self.build_spec = BuilderSpec(self.specs)

        self.images = {}
        self.metas = {}
        self.images_built = []
        self.images_dep = {}
        self.build_history = {}

        # sanity check
        self.images_dirs = []
        with os.scandir(path) as it:
            for entry in it:
                if not entry.is_file() and not entry.name.startswith('.'):
                    self.images_dirs.append(entry)
        #assert len(self.specs['images']) == len(self.images_dirs)
        # TODO: maybe more checks

    def build_img(self, image_name, build_path, build_args, plan_name, image_tag):
        # Go to build
        print(f'\n*** Started building "{image_tag}" ***')
        image, meta = dbuild(
            path=build_path,
            build_args=build_args,
            image_tag=image_tag,
            nocache=False
        )
        self.images[image_name] = image
        self.images_built.append(image_tag)
        self.build_history[image_name+plan_name] = image_tag
        return meta

    def process_meta(self, meta, image_name, build_args, image_tag):
        if meta:
            if 'BASE_TAG' in build_args:
                dep_tag = build_args['BASE_TAG']
                dep_img_name = self.build_spec.imageDefs[image_name].depend_on.img_name
                dep_full_tag = f"{dep_img_name}:{dep_tag}"
                self.images_dep[image_tag] = dep_full_tag
            store_dict('image-dependency.json', self.images_dep)
        self.metas[image_name] = meta

    def __enter__(self):
        logger.info(
            f"Building image stack from {self.path} using {self.specs_fp}")

        build_params = self.build_spec.gen_build_args(
            self.path, self.git_suffix, self.images_changed)
        for build_param in build_params:
            image_name, build_path, build_args, plan_name, image_tag = build_param
            if not self.dry_run:
                # Go to build
                print(f'\n*** Started building "{image_tag}" ***')
                meta = self.build_img(
                    image_name, build_path, build_args, plan_name, image_tag)

                store_var('IMAGES_BUILT', self.images_built)
                self.process_meta(meta, image_name, build_args, image_tag)

    def __exit__(self, exc_type, exc_value, traceback):
        store_dict('builder-metainfo.json', self.metas)
        store_dict('build_history.json', self.build_history)


def run_build(stack_dir):
    images_changed = read_var('IMAGES_CHANGED')
    print('changed images are', images_changed)
    git_suffix = read_var('GIT_HASH_SHORT')
    builder = DockerStackBuilder(
        path=stack_dir, specs='spec.yml',
        images_changed=images_changed, git_suffix=git_suffix
    )
    builder.__enter__()
    builder.__exit__(None, None, None)


if __name__ == '__main__':
    # docker_client=docker.from_env()
    # image = dbuild(
    #     path='images\datahub-base-notebook',
    #     build_args={'PYTHON_VERSION': 'python-3.8.8'},
    #     image_tag='base:test',
    #     docker_client=docker_client
    # )
    # print(image)
    '''
    logging.basicConfig(filename='builder.log', level=logging.INFO)
    images_changed = read_var('IMAGES_CHANGED')
    git_suffix = read_var('GIT_HASH_SHORT')
    builder = DockerStackBuilder(
        path='images', specs='spec.yml',
        images_changed=images_changed, git_suffix=git_suffix
    )
    builder.__enter__()
    builder.__exit__(None, None, None)
    '''
    run_build()
