from genericpath import isfile
from os import path, environ
from glob import glob
from posixpath import basename
from yaml import dump
from typing import Dict, List
import logging
import docker
import pandas as pd

from scripts.v2.utils import *
from scripts.v2.tree import Node
from scripts.v2.docker_adapter import run_simple_command, __docker_client
from scripts.v2.git_helper import GitHelper     # has it been used?
from scripts.v2.fs import MANIFEST_PATH



logger = get_logger()

def run_outputs(node: Node, all_info_cmds:Dict) -> List[Dict]: 
    """Run info commands of each image and return outputs. Wrapper around run_simple_command()

    Args:
        node (Node): _description_
        all_info_cmds (Dict): all available info commands generated by load_spec()['all_info_cmds']

    Returns:
        List[Dict]: each Dict has description (str), output (str) of one image.
    """
    
    outputs = []
    for key in node.info_cmds:
        if key not in all_info_cmds.keys():
            logger.error(f"command definition of {key} in {node.image_name} not found in spec.yml; skip")
            continue

        cmd_output, cmd_success = run_simple_command(
            node,
            all_info_cmds[key]['command']
        )

        description = all_info_cmds[key]['description']
        outputs.append(dict(description=description, output=cmd_output))
    
    return outputs


def get_layers(image: docker.models.images.Image):
    """Helper function of get_layers_md_table

    Args:
        image (docker.models.images.Image): the actual image object, not image name

    Returns:
        pandas.Dataframe: to be further processed.
    """
    df = pd.DataFrame(image.history()).convert_dtypes()
    df['CMD'] = df['CreatedBy']
    df['CMD'] = df['CMD'].str.replace('|', '', regex=False)
    df['CMD'] = df['CMD'].str.replace('/bin/bash -o pipefail -c', '', regex=False)
    df['CMD'] = df['CMD'].str.replace('#(nop)', '', regex=False)
    df['CMD'] = '`' + df['CMD'].str.strip() + '`'
    df['createdAt'] = pd.to_datetime(df['Created'], unit='s')
    df['hSize'] = df['Size'].apply(
        lambda x: bytes_to_hstring(x) if x > 100 else f'{x} B'
    )
    df['cumSize'] = df['Size'][::-1].cumsum()[::-1]
    df['hcumSize'] = df['cumSize'].apply(
        lambda x: bytes_to_hstring(x) if x > 100 else f'{x} B'
    )
    df_ordered = (
        df.loc[df['Tags'].notna()[::-1].cumsum()[::-1] > 0, :]
        .iloc[::-1, :]
        .reset_index(drop=True)
    )
    df_ordered['elapsed'] = df_ordered['createdAt'].diff()
    df_ordered.loc[1, 'elapsed'] = pd.Timedelta(0)
    df_ordered['elapsed'] = df_ordered['elapsed'].apply(strfdelta)
    return df_ordered


def get_layers_md_table(node: Node, image: docker.models.images.Image) -> str:
    """Given a node, generate a table in markdown format

    Args:
        node (Node): _description_
        image (docker.models.images.Image): the actual image object, not image name

    Returns:
        str: DataFrame in Markdown-friendly string format.
    """
    print("Trying to docker get: ", node.image_name + ':' + node.image_tag)
    node.print_info()
    layers = get_layers(image)[
        ['createdAt', 'CMD', 'hSize', 'hcumSize', 'elapsed', 'Tags']
    ]   # panda Dataframe: select columns to keep
    layers.dropna(inplace=True)
    return layers.to_markdown()


def write_report(
    node: Node, 
    image: docker.models.images.Image, 
    all_info_cmds:Dict, 
    output_dir: str = MANIFEST_PATH
    ):
    """Call run_outputs(), then format and store the outputs to <image_fullname>.md
    Wrapper around run_outputs() and get_layers_md_table()

    Args:
        node (Node): _description_
        image (docker.models.images.Image): the actual image object, not image name
        all_info_cmds (Dict): all available info commands generated by load_spec()['all_info_cmds']
        output_dir: (str, optional). Default to 'manifests'

    Returns:
        None
    """
    outputs = run_outputs(node, all_info_cmds)
    expandable_head = """<details>\n<summary>Details</summary>\n"""
    expandable_foot = """</details>\n"""

    sections = []
    sections.append(get_layers_md_table(node, image))

    for output in outputs:
        is_long_output = output['output'].count('\n') > 30
        if is_long_output:
            sections.append(
f"""
## {output['description']}

{expandable_head}
```
{output['output']}
```
{expandable_foot}

"""
            )
        else:
            sections.append(
f"""
## {output['description']}

```
{output['output']}
```

"""
            )

    stitched = '\n'.join(sections).strip()
    manifest_fn = fulltag2fn(node.full_image_name)
    output_path = path.join(output_dir, f"{manifest_fn}.md")
    with open(output_path, 'w') as f:
        f.write(stitched)

    print(f"*** Individual wiki page {manifest_fn}.md successfully written.")


def update_Home(images_full_names: List[str], git_short_hash: str) -> bool:
    """update Home.md (the page on https://github.com/ucsd-ets/datahub-docker-stack/wiki)

    Args:
        images_full_names (List[str]): a list of full image names (successfully built & tested). 

    Returns:
        bool: success/failure
    """

    if not images_full_names:
        logger.info(f"commit {git_short_hash} has no successful image to update Home.md")
        return True
    
    repo_url = f"https://github.com/ucsd-ets/datahub-docker-stack"
    # repo_url = f"https://github.com/{environ['GITHUB_REPOSITORY']}"
    
    # 1st column: commit link [git_short_hash](LINK)
    
    cell_commit = url2mdlink(repo_url + '/commit/' + git_short_hash, f"`{git_short_hash}`")

    # 2nd column: images full name
    cell_images = list2cell([f"`{image}`" for image in images_full_names])

    # 3rd column: image wiki page link ["LINK"](LINK)
    def wiki_doc2link(fullname: str) -> str:
        """ Helper function
        Given: ucsdets/rstudio-notebook:2023.1-7d75f9f
        Returns: [Link](https://github.com/ucsd-ets/datahub-docker-stack/wiki/ucsdets-rstudio-notebook-2023.1-7d75f9f)
        """
        assert fullname.count(':') == 1 and fullname.count('/') <= 1, \
            f"Wrong image full name format: {fullname}"
        fullname = fullname.replace(':', '-').replace('/', '-')
        link = url2mdlink(repo_url + '/wiki/' + fullname, 'Link')
        return link

    try:
        manifests_links = [wiki_doc2link(fullname=image) for image in images_full_names]
    except AssertionError as e:
        logger.error(e)
        return False
    
    cell_manifests = list2cell(manifests_links)

    # group 3 columns together
    latest_row = (cell_commit, cell_images, cell_manifests)

    # Read old content, Update, Write back
    try:
        with open(path.join('wiki', 'Home.md'), 'r') as f:
            doc_str = f.read()
        
        # 2nd arg of insert_row() takes in List[Tuple], each of which is a new 'latest_row'
        latest_doc = insert_row(doc_str, [latest_row])

        with open(path.join('wiki', 'Home.md'), 'w') as f:
            f.write(latest_doc)
    except Exception as e:
        logger.error(e)
        print("Error when updating Home.md")
        return False

    return True

def insert_history():
    with open(path.join('wiki', 'Home.md'), 'r') as f:
        doc_str = f.read()

    latest_row = compile_history()
    # compile history() returns 3 var, so lastest row is a tuple
    latest_doc = insert_row(doc_str, [latest_row])
    # latest_doc = insert_row(doc_str, latest_row)

    with open(path.join('wiki', 'Home.md'), 'w') as f:
        f.write(latest_doc)

def run_manifests(images_built: List[str]):
    # FIXME abstract stack_dir
    stack_dir = 'images'
    image_deps = json2series(read_dict('image-dependency.json'), 'dep', 'image')
    store_series(image_deps, 'image-dependency')

    # Write image dependency table to wiki
    dep_table_fp = 'wiki/Image Dependency.md'
    if isfile(dep_table_fp):
        old_csv = strip_csv_from_md(dep_table_fp)
        csv_concat(old_csv, 'artifacts/image-dependency.csv', 'artifacts/image-dependency-updated.csv')
        csv_embed_markdown('artifacts/image-dependency-updated.csv', dep_table_fp, 'Image Dependency')
    else:
        csv_embed_markdown('artifacts/image-dependency.csv', dep_table_fp, 'Image Dependency')
    
    specs = get_specs(path.join(stack_dir, 'spec.yml'))
    for image in images_built:
        keys = list(filter(lambda x: x in image, specs['images']))
        assert len(keys) == 1
        image_key = keys[0]
        print('Running image manifest for', image)
        run_report(specs, image_key, image=image)

    insert_history()

if __name__ == "__main__":
    print("wiki.py: Import Success")
    client = docker.from_env()
    img_obj = client.images.get('ucsdets/datahub-docker-stacks:pushtest')
    
    test_node = Node(
        image_name='ucsdets/datahub-docker-stacks',
        image_tag='pushtest',
        filepath='tests/v2',
        children=[],
        rebuild=False,
        image_built=False,
        build_args={},
        integration_tests=False,
        dockerfile='test.Dockerfile',
        info_cmds=['PY_VER', 'CONDA_INFO', 'CONDA_LIST']
    )
    all_info_cmds = {
        'PY_VER': {
            'description': 'Python Version',
            'command': 'python --version'
        },
        'CONDA_INFO': {
            'description': 'Conda Info',
            'command': 'conda info'
        },
        'CONDA_LIST': {
            'description': 'Conda Packages',
            'command': 'conda list'
        },
    }
    
    write_report(node=test_node, image=img_obj, all_info_cmds=all_info_cmds)
