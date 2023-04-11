# Manifest_logic

## Report: wiki page of individual image

`run_report()`, which calls `run_outputs()`, is called on a single image.

Operations like login(), build(), push() can be done with a docker client
`docker_client.from_env()` only.  
But for other operations like executing command `conda list`, we need to
create a container for an image.

Related files:

- docker_runner.py
- conftest.py

In runner.py, build_and_test_containers() BFS loop:

- write_report() -> run_outputs() -> run_simple_command()  
- write_report() -> get_layers_md_table() -> get_layers()

## Manifest: wiki page for global information

Related functions in manifests.py:

helpers:

- compile_history(compile_tag_history = False):
- insert_history(markdown_fp):
- update_history():

doit functions:

- run_manifests(stack_dir):
- run_stable_manifests():

**Problem:** these functions are not called on individual image

Originally, run_manifests()

1. load `IMAGES_BUILT`
2. read `image-dependency.json` and write a dependency table to `wiki/Image Dependency.md`
3. generate report (individual markdown file) for each image
4. concatenate commit || [images full name] || [their respective wiki link] and write to `wiki/Home.md`

But is the [image dep table](https://github.com/ucsd-ets/datahub-docker-stack/wiki/Image-Dependency) useful?
Repeated info.
