from os import path

from scripts.utils import read_var
from scripts.utils import get_specs
from scripts.docker_runner import DockerRunner


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
    output_path = path.join(output_dir, f'{image_key}.md')
    with open(output_path, 'w') as f:
        f.write(stitched)


def run_manifests():
    images = read_var('IMAGES_BUILT')
    
    specs = get_specs(path.join('images', 'spec.yml'))
    for image in images:
        keys = list(filter(lambda x: x in image, specs['images']))
        assert len(keys) == 1
        image_key = keys[0]
        run_report(specs, image_key, image=image)


if __name__ == '__main__':
    specs = get_specs('images\spec.yml')
    run_report(specs, 'datahub-base-notebook')
