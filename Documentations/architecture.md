# Architecture

This document will give a high-level overview of the datahub-docker-stacks project. 

## Overview

The intent is to create a reliable way of maintaining a "stack" of Docker 
images, each of which can be the "base" image of another (DAG), with minimial 
human supervision. Essentially, in the scenario that a lot of images are using 
an image as the base, and the parent image requires an update, it will progate 
the change and re-build the dependent images using the latest version. 

## Jupyter's Docker Stack

The [docker-stacks](https://github.com/jupyter/docker-stacks) by the Jupyter team 
is a very similar project maintaining ~8 Docker images for Jupyter notebook/lab. 
However, as of now, the project re-builds the entire stack all at 
once regardless of which image source is changed, and results in a very long 
turnaround time. There are plans (
    [#1203](https://github.com/jupyter/docker-stacks/issues/1203),
    [#1407](https://github.com/jupyter/docker-stacks/issues/1407),
    [milestone](https://github.com/jupyter/docker-stacks/milestone/1)
) to optimize this "monolithic" build pattern but work has not yet began. So 
the our pipeline is using an entirely different approach. Thanks to the Jupyter 
team for putting together this project.

## Core Components

The project utilizes several technologies and libraries that are either publicly 
available or open-sourced. We use Github Actions for running the whole pipeline 
and building the Docker images. DockerHub is where the images are hosted. 
[Doit](https://github.com/pydoit/doit) is the command-line interface that is 
used to execute tasks. And we use [Docker SDK for Python](https://docker-py.readthedocs.io/en/stable/) for interfacing with the local Docker engine and Python 3.8
to run the pipeline. For testing, we use pytest.

- Docker Engine / Docker Desktop
- Python > 3.8

## Directory Structure

```
├── .github
│   └── workflows
│       └── main.yml            (workflow spec for Github Actions)
├── images
│   ├── datahub-base-notebook
│   │   ├── Dockerfile
│   │   ├── ...
│   │   └── test                (image acceptance tests)
│   │       └── ...
│   ├── datascience-notebook
│   │   ├── Dockerfile
│   │   ├── test
│   │   │   ├── data
│   │   │   │   └── *.ipynb     (notebook run)
│   │   │   └── test_notebooks.py (interface for notebook test)
│   ├── scipy-ml-notebook
│   │   └── Dockerfile
│   ├── tests_common            (acceptance tests applied to all)
│   │   └── ...
│   ├── conftest.py             (pytest setup for image acceptance)
│   └── spec.yml                (image spec file for current stack)
├── model                       (data structures)
│   ├── imageDef.py             - (ds for images)
│   └── spec.py                 - (ds for stack spec)
├── scripts
│   ├── LICENSE.md
│   ├── docker_builder.py       (interface for builds)
│   ├── docker_info.py          (interface for detailed image info)
│   ├── docker_pusher.py        (interface for pushing)
│   ├── docker_runner.py        (interface for running commands in image)
│   ├── docker_tester.py        (interface for running acceptance tests)
│   ├── git_helper.py           (query git for hash and changed files)
│   ├── manifests.py            (interface for creating manifest)
│   ├── requirements.txt        (pip requirements)
│   └── utils.py                (various utilities)
├── tests                       (tests for the workflow)
│   ├── README.md
│   ├── data
│   │   └── specs               (spec file test samples)
│   │   │   ├── spec_0.yaml
│   │   │   ├── spec_1.yaml
│   │   │   ├── spec_2.yaml
│   │   │   └── spec_3.yaml
│   │   ├── stack_0             (stack folder test samples)
│   │   │   ├── base
│   │   │   │   └── Dockerfile
│   │   │   ├── branch
│   │   │   │   └── Dockerfile
│   │   │   ├── leaf
│   │   │   │   └── Dockerfile
│   │   │   └── spec.yml
│   │   ├── stack_1
│   │   └── stack_...
│   ├── test_docker.py
│   ├── test_model.py
│   └── test_step_build.py
├── artifacts   (untracked)
├── manifests   (untracked)
├── logs        (untracked)
├── wiki        (Untracked)
├── Architecture.md             (this file)
├── dodo.py                     (Doit task definition and config)
├── plan.md
└── README.md
```

## Pipeline

Updating Docker images is very similar to updating an open-source library. 
Build, test, and deploy will be building the Docker images, testing images if 
they have the right contents and features, and lastly publishing it on 
Dockerhub. We also add in steps to generate image "manifests" for listing out 
package informations and publishing them to the project wiki, and steps to 
dump logs and various artifacts that were produced in the Action run into 
zip files and uploaded for reference.

For a more detailed version of the pipeline, you can check out 
`.github/workflows/main.yml` for steps to setup the environment and a thorough 
list of commands

## Image Stack Details

For the pipeline to recognize the stack, there should be a dedicated directory 
preferably called `images/` that contains sources for images in the stack.

- One sub-directory under `images/` equals one unique docker image
- Under sub-directory, there should be a `Dockerfile` with the steps to build the image
- `Dockerfile` should be using build-args to dynamically point to arbitary base 
image (see sample for details)
- Test can be provided for each image as `test` under their source folder and 
for all images (`tests_common` under `images/`). Include the provided 
`conftest.py` for them to work
- A `spec.yml` file detailing how the images are structured
- The image sub-directories created should be equal to the keys under `images` in the yaml spec
- Plans can be enabled to serve two or more tracks/versions of the same image
at the same time under one docker image name. Custom tag prefix are used to 
identify them
- Manifests are a way to list out information about an image. These can be 
defined by a name and a corresponding command to run inside the container.
- Different images can include different sets of manifests.

## Image Customization

- Build args are expected to be used in dynamic image tags for base refs 
- They can also be used for swapping out variables for different plans
- Can put custom variables in spec yaml file.

## Image Update Details

- Every newly pushed images will get a git-hash stamp at the end of the tag
(`ucsdets/datahub-base-notebook:2021.2-5f71d3b`)
- The `FROM` statement in `Dockerfile` will include `ARG` in the image ref to
support arbitary tags at run-time. This allows for fixating the Dockerfile 
while changing the base ref at any time.
- When a dependent images gets its source updated, instead of building the base 
image again, only build the dependent image by changing the base ref to the 
old remote tag of the image and build from there.
- `stable` tags will be given to the lastest built image in each image/plan for 
use in production.

## Pipeline Details

- When the workflow is first triggered, the doit will create subfolders in the
project root for storing files. (`artifacts/`, `manifests/`, `logs/`)
- `artifacts/` is storing strings and lists for persisting variables between 
doit tasks, also stores meta information for building, etc
- The pipeline will then look for changes in the `images/` in the latest git 
commit determine which images' source was changed and will be used to determine 
what images need to be updated. The list of changed images is kept in 
`artifacts/IMAGES_CHANGED`.
- If the pipeline script or the workflow file was changed, the pipeline will 
default to re-building the whole stack.
- As a result, only push commits to Github one at a time as Github will only 
trigger on the lastest commit in a push event. 
- The wiki is cloned to get the dependency table.
- The list of images that need to be built is calculated and is then built 
in the order according to the dependency table.
- The list of images that were built is then store in `artifacts/IMAGES_BUILT`.
- Output, size, and timestamp for each layer built is also stored as a json.
- Tests are then run according to the source in `tests_common` or individual 
`test` folders inside each image source folder. 
- Tests from upstream (base images) will be added to the current image to be 
tested again.
- All the tests are run regardless of any of them does not pass.
- Images that fails any test will be included in `artifacts/IMAGES_TEST_ERROR` 
and images that pass all tests will be included in `artifacts/IMAGES_TEST_PASSED`.
- The workflow will only proceed if and only if all tests for all built images 
versions are passed.
- Image manifests are generated and store under `manifests/`
- Images that were built are then pushed to DockerHub.
- Manifests are then moved to wiki folder and committed.
- Workflow will archive artifacts for reference and debugging 
(`artifacts/`, `manifests/`, `logs/`)
