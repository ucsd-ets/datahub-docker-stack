from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Node:
    image_name: str
    repo_name: str
    tag_name: str
    filepath: str
    children: List
    build_args: Dict
    rebuild: bool
    image_built: bool
    integration_tests: bool


@dataclass
class Result:
    success: bool
    message: str


def load_spec(spec_filepath) -> dict:
    pass


def build_tree(spec_yaml: dict) -> Node:
    pass


def mark_rebuild(root: Node):
    pass

