import itertools
import re
import os; pjoin = os.path.join
import logging

import docker
from docker.utils.json_stream import json_stream
from docker.errors import BuildError

from scripts.utils import get_specs


logger = logging.getLogger(__name__)

def dbuild(
    path: str, image_tag: str, build_args=None, 
    docker_client=docker.from_env(), verbose=True
):
    """
    Adopted from https://github.com/docker/docker-py/blob/master/docker/models/images.py
    """
    try:
        logger.info(f"Begin build for {pjoin(path, 'Dockerfile')}")
        resp = docker_client.api.build(
            path=path, dockerfile='Dockerfile', tag=image_tag,
            buildargs=build_args,
            nocache=False,
        )
        last_event = None
        image_id = None
        result_stream, internal_stream = itertools.tee(json_stream(resp))
        for chunk in internal_stream:
            if 'error' in chunk:
                raise BuildError(chunk['error'], result_stream)
            if 'stream' in chunk:
                if verbose:
                    print(chunk['stream'], end='')
                match = re.search(
                    r'(^Successfully built |sha256:)([0-9a-f]+)$',
                    chunk['stream']
                )
                if match:
                    image_id = match.group(2)
            last_event = chunk
        if image_id:
            image = docker_client.images.get(image_id)
            logger.info(f"Successfully finish build for {image}")
            return image

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
            # FIXME:
            image_tag = f"{image_spec['image_name']}:{self.specs['plans'][self.plan]['tag_prefix']}-111111"
            image_spec['image_tag'] = image_tag
            build_args = {}
            if 'depend_on' in image_spec:
                base_full_tag = self.specs['images'][image_spec['depend_on']]['image_tag']
                custom_tag = base_full_tag.split(':')[1]
                build_args.update(BASE_TAG=custom_tag)
            if 'dbuild_env' in image_spec:
                dbuild_env = image_spec['dbuild_env']
                if 'common' in dbuild_env.keys():
                    build_args.update(dbuild_env['common'])
                if self.plan in dbuild_env.keys():
                    build_args.update(dbuild_env[self.plan])
            
            if not self.dry_run:
                # Go to build
                print(build_args)
                logger.info('') # TODO: fill meta info
                image = dbuild(
                    path=path,
                    build_args=build_args,
                    image_tag=image_tag,
                )
                self.images[short_name] = image
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass

if __name__ == '__main__':
    # docker_client=docker.from_env()
    # image = dbuild(
    #     path='images\datahub-base-notebook',
    #     build_args={'PYTHON_VERSION': 'python-3.8.8'},
    #     image_tag='base:test',
    #     docker_client=docker_client
    # )
    # print(image)

    with DockerStackBuilder(path='images', specs='spec.yml', plan='PYTHON38') as builder:
        pass
