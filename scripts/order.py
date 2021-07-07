import yaml
from collections import deque


def get_specs(f_yaml):
    """
    Parse specs from yaml file name to dict
    """
    with open(f_yaml, 'r') as f:
        specs = yaml.safe_load(f)
    return specs


class DockerImageDef:
    def __init__(self, name, depend_on=None) -> None:
        self.name = name
        self.depend_on = depend_on
        self.downstream = []

    def __repr__(self) -> str:
        return f'DockerImageDef({self.name})'

    def subtree_order(self):
        """pre-order DFS"""
        stack = deque()
        stack.append(self)
        order = []
        while stack:
            curr = stack.pop()
            order.append(curr.name)
            for child in curr.downstream:
                stack.append(child)
        return order

    def get_level_order(self):
        '''BFS'''
        queue = [self]
        order = {}
        cnt = 0
        while queue:
            curr = queue.pop(0)
            for child in curr.downstream:
                queue.append(child)
            order[curr] = cnt
            cnt += 1
        return order


def build_tree(specs):
    root = None
    image_specs = specs['images']
    images = {}
    for key, image in image_specs.items():
        if key not in images:
            curr_image = DockerImageDef(image['image_name'])
            images[key] = image
        else:
            curr_image = images[key]
        if 'depend_on' in image.keys():
            dep_image_name = image['depend_on']
            if dep_image_name not in images:
                dep_image = DockerImageDef(dep_image_name)
                images[dep_image_name] = dep_image
            else:
                dep_image = images[dep_image_name]
            curr_image.depend_on = dep_image
            dep_image.downstream.append(curr_image)
        else:
            root = key
    assert root is not None
    return images, root
    '''
    for key, image in image_specs.items():
        if 'depend_on' in image.keys():
            image_base = images[image['depend_on']]
            image = DockerImageDef(image['image_name'], depend_on=image_base)
            image_base.downstream.append(image)
        else:
            image = DockerImageDef(image['image_name'])
        images[key] = image
    '''


if __name__ == '__main__':
    specs = get_specs('images\spec.yml')
    tree = build_tree(specs)
