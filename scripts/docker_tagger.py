import docker
from typing import List

from scripts.utils import read_history, get_images_for_tag
from scripts.utils import read_var, store_var
from scripts.docker_pusher import push_images


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
        print(f'String =\'{full_name}\'')
        print(f'String =\'{img}\'')
        print(f'String =\'{tag}\'')
        cli.images.pull(img, tag)


def tag_image(
        cli: docker.client.DockerClient,
        img_name_original: str,
        img_tag_full_name: str
):
    assert ':' in img_tag_full_name

    img = cli.images.get(img_name_original)
    repo, tag = img_tag_full_name.split(':')

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

    prepull_image(cli, list(replace_dict.keys()))

    tagged = []
    for img_orig, img_new in replace_dict.items():
        tag_image(cli, img_orig, img_new)
        tagged.append(img_new)
        store_var('IMAGES_TAGGED', tagged)

    push_images(cli, [(cli.images.get(img), img) for img in tagged])
