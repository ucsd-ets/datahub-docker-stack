from genericpath import isfile
from os import path, environ
from glob import glob
from posixpath import basename
from yaml import dump
import logging
import docker
import pandas as pd

from scripts.v2.utils import *
from scripts.v2.tree import Node
from scripts.v2.docker_adapter import run_simple_command, __docker_client__
from scripts.v2.git_helper import GitHelper     # has it been used?



logger = logging.getLogger('datahub_docker_stacks')

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
            container,
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


def get_layers_md_table(node: Node, cli: docker.DockerClient = __docker_client__) -> str:
    """Given a node, generate a table in markdown format

    Args:
        node (Node): _description_
        cli (docker.DockerClient, optional): Defaults to __docker_client__.

    Returns:
        str: DataFrame in Markdown-friendly string format.
    """
    layers = get_layers(cli.images.get(node.image_name))[
        ['createdAt', 'CMD', 'hSize', 'hcumSize', 'elapsed', 'Tags']
    ]   # panda Dataframe: select columns to keep
    layers.dropna(inplace=True)
    return layers.to_markdown()


def write_report(node: Node, all_info_cmds:Dict, output_dir='manifests'):
    """Call run_outputs(), then format and store the outputs to <image_fullname>.md
    Wrapper around run_outputs() and get_layers_md_table()

    Args:
        node (Node): _description_
        all_info_cmds (Dict): all available info commands generated by load_spec()['all_info_cmds']
        output_dir: (str, optional). Default to 'manifests'

    Returns:
        None
    """
    outputs = run_outputs(node, all_info_cmds)
    expandable_head = """<details>\n<summary>Details</summary>\n"""
    expandable_foot = """</details>\n"""

    sections = []
    sections.append(get_layers_md_table(node))

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
    manifest_fn = fulltag2fn(image)
    output_path = path.join(output_dir, f"{manifest_fn}.md")
    with open(output_path, 'w') as f:
        f.write(stitched)

    print(f"*** Individual wiki page {manifest_fn}.md successfully written.")






if __name__ == "__main__":
    print("wiki.py: Import Success")