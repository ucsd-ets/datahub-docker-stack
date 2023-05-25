from dataclasses import dataclass, field
from typing import List, Dict
import yaml
from collections import defaultdict

from scripts.utils import get_logger

logger = get_logger()


@dataclass
class Node:
    # required args
    image_name: str
    git_suffix: str
    children: List = field(default_factory=list)
    build_args: Dict = field(default_factory=dict)
    # optioanl args
    filepath: str = ""
    dockerfile: str = 'Dockerfile'
    rebuild: bool = False
    image_built: bool = False  # determined during runtime
    integration_tests: bool = False
    image_tag: str = ""  # determined during runtime
    info_cmds: List = field(default_factory=list)
    prune: bool = False

    @property
    def full_image_name(self):
        return self.image_name + ':' + self.image_tag

    # TODO: temporary, should be removed later
    @property
    def stable_image_name(self):
        return self.image_name + ':' + self.image_tag[:6] + '-stable' 

    def print_info(self):
        print( f"""image_name: {self.image_name},
                git_suffix: {self.git_suffix}, 
                docker_tag: {self.image_tag},
                build_args: {self.build_args},
                filepath: {self.filepath},
                rebuild: {self.rebuild},
                integration_tests: {self.integration_tests},
                info_cmds: {self.info_cmds},
                children: {[child.image_name for child in self.children]}\n"""
        )
        for child in self.children:
            child.print_info()

def load_spec(spec_filepath="images/spec.yml") -> dict:
    """Parse specs from yaml file name to dict

    Args:
        spec_filepath (str, optional): full path (dir/filename) of the yaml file. 
            Defaults to "images/spec.yml".

    Returns:
        dict: 

    Credit:
        scripts/utils.py::get_specs()
    """
    with open(spec_filepath, 'r') as f:
        specs = yaml.safe_load(f)
    return specs


def build_tree(spec_yaml: dict, images_changed: List[str], git_suffix: str='gitnull') -> Node:
    """Generate a dependency tree for the python doit pipeline

    Args:
        spec_yaml (dict): a dict generated by load_spec()
        images_changed (List[str]): which images are changed; WITHOUT "ucsdets/" prefix
        git_suffix (str): the short-version git commit hashtag.

    Returns:
        Node: the root node. 

    NOTE:
        Our use case has only 1 single base image: ucsdets/datahub-base-notebook
    """
    if 'images' not in spec_yaml:
        raise KeyError("Specification of images should be under root level. \
            Please check your yaml/yml file")
    images = spec_yaml['images']
    dep = defaultdict(list)     # local helper dict to store dependency (parent: [children])

    # find root & store dependencies: single-root solution for now:
    ROOT_IMAGE = "NULL"
    for key, info in images.items():
        # use key instead of info['image_name'], since we want to use
        # datahub-base-notebook instead of ucsdets/datahub-base-notebook
        # prefix "ucsdets/" will be appened in Node Constructor
        if "depend_on" not in info:
            # root
            ROOT_IMAGE = key
        else:
            dep[info['depend_on']].append(key)

    # single-root check:
    if ROOT_IMAGE != "datahub-base-notebook":
        logger.error(f"Expect base image to be datahub-base-notebook but got {ROOT_IMAGE}")

    ### Helper function
    def build_node(img_name: str, parent_rebuild: bool, repo: str="ucsdets/") -> Node:
        """Helper function that builds the node recursively.

        Args:
            img_name (str): image name string
            parent_rebuild (bool): bool rebuild of its parent

        Returns:
            Node: The Node and its children Nodes with sufficient build info
        """
        
        should_rebuild = parent_rebuild or (img_name in images_changed)
        should_prune = images[img_name].get("prune", False)
        should_integration = images[img_name].get("integration_tests", False)
        children_nodes = [] # leaf node has empty by default
        if img_name in dep:
            # non-leaf: build all children before passing to Constructor
            children_nodes = [build_node(child_name, should_rebuild) 
                                for child_name in dep[img_name]]
        
        
        # default to an empty dict if build_args doesn't exist
        build_args = images[img_name]['build_args'] if 'build_args' in images[img_name] else {}
        # default to an empty list if info_commands doesn't exist
        cmd_list = images[img_name]['info_cmds'] if "info_cmds" in images[img_name] else []

        return Node(
            image_name=repo + img_name,
            git_suffix=git_suffix,
            children=children_nodes,
            build_args=build_args,
            rebuild=should_rebuild,
            filepath='images/' + img_name,
            integration_tests=should_integration,
            info_cmds=cmd_list,
            prune=should_prune
        )
    ### ********************************* ###
    
    return build_node(ROOT_IMAGE, False)


if __name__ == "__main__":
    print("Import Success")
    d = load_spec("images/spec.yml")
    root_node = build_tree(d, [], "c11a915")
    root_node.print_info()