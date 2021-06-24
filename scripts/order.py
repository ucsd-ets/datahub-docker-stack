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
            order.append(curr)
            for child in curr.downstream:
                stack.append(child)
        return order
        


def build_tree(specs):
    image_specs = specs['images']
    images = {}
    for key, image in image_specs.items():
        if 'depend_on' in image.keys():
            image_base = images[image['depend_on']]
            image = DockerImageDef(image['image_name'], depend_on=image_base)
            image_base.downstream.append(image)
        else:
            image = DockerImageDef(image['image_name'])
        images[key] = image
    return images


if __name__ == '__main__':
    specs = get_specs('images\spec.yml')
    tree = build_tree(specs)
