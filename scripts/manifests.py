from genericpath import isfile
from os import path, environ
from glob import glob
from posixpath import basename

from yaml import dump

from scripts.utils import list2cell, read_var, read_dict, store_series, json2series
from scripts.utils import csv_embed_markdown, strip_csv_from_md, csv_concat
from scripts.utils import url2mdlink, fulltag2fn, insert_row
from scripts.utils import get_specs
from scripts.docker_runner import DockerRunner
from scripts.git_helper import GitHelper
from scripts.docker_info import get_layers_md_table


def run_outputs(specs, image_key, image=None):
    """
    Run commands listed in manifests according to list
    """
    image_specs = specs['images'][image_key]
    if image is None:
        image = image_specs['image_name']
    manifest_all = specs['manifests']
    manifest_selected = image_specs['manifests']
    
    with DockerRunner(image) as container:
        outputs = []
        for key in manifest_selected:
            if key not in manifest_all.keys():
                continue
            output = DockerRunner.run_simple_command(
                container,
                manifest_all[key]['command']
            )
            description = manifest_all[key]['description']
            outputs.append(dict(description=description, output=output))
    
    return outputs

def run_report(specs, image_key, image=None, output_dir='manifests'):
    image_specs = specs['images'][image_key]
    if image is None:
        image = image_specs['image_name']
    outputs = run_outputs(specs, image_key, image=image)
    expandable_head = """<details>\n<summary>Details</summary>\n"""
    expandable_foot = """</details>\n"""

    sections = []

    sections.append(get_layers_md_table(image))

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


def compile_history(compile_tag_history = False):
    repo_url = f"https://github.com/{environ['GITHUB_REPOSITORY']}"
    if compile_tag_history == True:
        cell_commit = ""
        img_source = 'IMAGES_TAGGED'
        orig_source = 'IMAGES_ORIGINAL'
        orig_images = list2cell([f"`{image}`" for image in read_var(orig_source)])
    else:
        git_short_hash = read_var('GIT_HASH_SHORT')
        cell_commit = url2mdlink(repo_url + '/commit/' + git_short_hash, f"`{git_short_hash}`")
        img_source = 'IMAGES_BUILT'

    cell_images = list2cell([f"`{image}`" for image in read_var(img_source)])
    if compile_tag_history:
        cell_images += '|' + orig_images

    """
    # glob(path.join()) will return a list of manifests md in random order, 
    # causing mismatch with images
    manifests_dir = 'manifests'
    manifests_fp = glob(path.join(manifests_dir, '*.md'))
    manifests_doc_names = [path.splitext(path.basename(doc))[0] for doc in manifests_fp]
    """

    # to align the order of cell_images and cell_manfests, we can directly read "name" from IMAGES_BUILT also.
    # read_var('IMAGES_BUILT') gives a list of ucsdets/{image_name}:{tag} 
    # what we want for "name" after '/wiki/' is sth like ucsdets-{image_name}-{tag}
    manifests_doc_names = [image.replace(':', '-').replace('/', '-') for image in read_var(img_source)]
    print("manifests_doc_names:  ", manifests_doc_names)

    
    manifests_links = [url2mdlink(repo_url + '/wiki/' + name, 'Link') for name in manifests_doc_names]
    cell_manifests = list2cell(manifests_links)

    return cell_commit, cell_images, cell_manifests


def insert_history(markdown_fp):
    with open(path.join('wiki', 'Home.md'), 'r') as f:
        doc_str = f.read()

    latest_row = compile_history()
    # compile history() returns 3 var, so lastest row is a tuple
    # latest_doc = insert_row(doc_str, [latest_row])
    latest_doc = insert_row(doc_str, latest_row)

    with open(path.join('wiki', 'Home.md'), 'w') as f:
        f.write(latest_doc)

def update_history():
    # This function read tagging info from artifacts/IMAGES_TAGGED
    # and update the stable.md page
    latest_row = compile_history(compile_tag_history=True)
    header = ['| Image | Based On | Manifest |']
    divider = ['| :- | :- | :- |']
    """
    # lastest row is a single tuple with 3 str, from compile_history()
    content = ['|'.join(line_tup) +
               '|' for line_tup in [latest_row]]
    """
    content = ['|'.join(latest_row) + '|']
    content = header + divider + content 
    doc = "\n".join(content)
    print(latest_row)
    with open(path.join('wiki', 'Stable Tag.md'), 'w') as f:
        f.write(doc)

def run_manifests(stack_dir):
    images = read_var('IMAGES_BUILT')
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
    for image in images:
        keys = list(filter(lambda x: x in image, specs['images']))
        assert len(keys) == 1
        image_key = keys[0]
        print('Running image manifest for', image)
        run_report(specs, image_key, image=image)

    insert_history('wiki/Home.md')

def run_stable_manifests():
    stable_images = read_var('IMAGES_TAGGED')
    print(stable_images)
    specs = get_specs(path.join('images', 'spec.yml'))
    for image in stable_images:
        keys = list(filter(lambda x: x in image, specs['images']))
        assert len(keys) == 1
        image_key = keys[0]
        print('Running image manifest for', image)
        print('image key is', image_key)
        run_report(specs, image_key, image=image)
    update_history()


