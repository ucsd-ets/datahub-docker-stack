from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Node:
    image_name: str = ''
    image_tag: str = ''
    filepath: str = ''
    children: List = field(default_factory=list)
    build_args: Dict = field(default_factory=dict)
    rebuild: bool = False
    image_built: bool = False
    integration_tests: bool = False
    dockerfile: str = 'Dockerfile'
    registry: str = 'https://index.docker.io/v1/'


def load_spec(spec_filepath) -> dict:
    pass


def build_tree(spec_yaml: dict) -> Node:
    pass


def mark_rebuild(root: Node):
    pass

