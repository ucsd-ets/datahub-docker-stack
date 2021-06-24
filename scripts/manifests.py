import yaml

from scripts.docker_runner import DockerRunner

def get_specs(f_yaml):
    """
    Parse specs from yaml file name to dict
    """
    with open(f_yaml, 'r') as f:
        specs = yaml.safe_load(f)
    return specs

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

def run_report(specs, image_key, image=None):
    image_specs = specs['images'][image_key]
    if image is None:
        image = image_specs['image_name']
    outputs = run_outputs(specs, image_key, image=image)
    sections = [
f"""
## {output['description']}

```
{output['output']}
```

"""
        for output in outputs
    ]
    stitched = '\n'.join(sections).strip()
    with open('manifest.md', 'w') as f:
        f.write(stitched)


    

if __name__ == '__main__':
    specs = get_specs('images\spec.yml')
    run_report(specs, 'datahub-base-notebook', image='scipy-ml')