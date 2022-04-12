import docker
from typing import List
import logging
from scripts.utils import read_history, get_images_for_tag
from scripts.utils import read_var, store_var
from scripts.docker_pusher import push_images, docker_login
import os

logger = logging.getLogger(__name__)


def prepull_image(
        cli: docker.client.DockerClient,
        images: List[str]
):
    for full_name in images:
        print(f'Pulling {full_name}')
        assert ':' in full_name

        img, tag = full_name.split(':')
        img = img.lstrip()
        tag = tag.rstrip()

        cli.images.pull(img, tag)


def tag_image(
        cli: docker.client.DockerClient,
        img_name_original: str,
        img_tag_full_name: str
):
    assert ':' in img_tag_full_name
    img_name_original = img_name_original.strip()
    img = cli.images.get(img_name_original)
    repo, tag = img_tag_full_name.split(':')
    repo = repo.strip()
    assert img.tag(repository=repo, tag=tag)


def run_tagging(commit_tag, keyword, tag_replace, dry_run=False):
    assert all([commit_tag, keyword, tag_replace]), 'None as input'

    cli = docker.from_env()
    history = read_history()
    replace_dict = get_images_for_tag(
        history, commit_tag, keyword, tag_replace)

    if dry_run:
        print(replace_dict)
        return

    print("prepulling images")
    prepull_image(cli, list(replace_dict.keys()))
    print("finished prepull")

    tagged = []
    for img_orig, img_new in replace_dict.items():
        print(f'Tagging {img_orig} to {img_new}')
        tag_image(cli, img_orig, img_new)
        tagged.append(img_new)
        store_var('IMAGES_TAGGED', tagged)

    print("finished tagging")
    tag_list = [(cli.images.get(img.strip()), img.strip()) for img in tagged]

    print("pushing newly tagged images")
    docker_login(cli, os.environ['DOCKERHUB_USER'], os.environ['DOCKERHUB_TOKEN'])
    push_images(cli, tag_list)
    print("finished pushing, job complete")
