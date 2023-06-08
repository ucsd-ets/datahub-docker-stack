# DataHub Docker Stack: Repository Architecture

This document will give a high-level overview of the datahub-docker-stacks repository.

## Overview

The intent is to create a reliable way of maintaining a "stack" of Docker
images, each of which can be the "base" image of another (thus resulting in a Directed Acyclic Graph),
with minimial human supervision. Essentially, in the scenario that a lot of images are using
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

```bash
├── .github
│   └── workflows # workflow spec for Github Actions. See actions.md
│       ├── main.yml
│       ├── tag.yml
│       └── test_gpu.yml         
├── Documentation  # Docs for each key component, in markdown
│   ├── ...
├── LICENSE.txt
├── README.md   # Home page, with table of contents of docs
├── dodo.py     # definition for more complex workflow task, use pydoit module
├── images      # All image definitions & resources. See images.md 
│   ├── change_ignore.json
│   ├── conftest.py    # pytest setup for image acceptance; by Jupyter Development Team (3rd party).
│   ├── datascience-notebook
│   │   ├── Dockerfile  # image definition for docker
│   │   ├── scripts     # .sh & .py scripts used for container setup
│   │   │   └── ...
│   │   ├── start-code-server.sh
│   │   └── test    # image acceptance tests
│   │       ├── data
│   │       │   └── test-notebook.ipynb
│   │       ├── test_container_options.py
│   │       ├── test_package_managers.py
│   │       ├── test_pandoc.py
│   │       ├── test_python.py
│   │       └── test_start_container.py
│   ├── rstudio-notebook
│   │   ├── Dockerfile
│   │   ├── integration_tests
│   │   │   ├── datascience-rstudio.Rmd
│   │   │   ├── knitter.sh
│   │   │   └── test_rstudio_ui.py
│   │   └── test
│   │       └── test_rstudio.py
│   ├── scipy-ml-notebook
│   │   ├── Dockerfile
│   │   ├── activate.sh
│   │   ├── cudatoolkit_env_vars.sh
│   │   ├── cudnn_env_vars.sh
│   │   ├── manual_tests
│   │   │   ├── pytorch_mtest.ipynb
│   │   │   └── tensorflow_mtest.ipynb
│   │   ├── run_jupyter.sh
│   │   ├── test
│   │   │   ├── __init__.py
│   │   │   ├── data
│   │   │   │   └── test_tf.ipynb
│   │   │   └── test_tf.py
│   │   └── workflow_tests
│   │       ├── test_pytorch.py
│   │       └── test_tf.py
│   ├── spec.yml        # image definition metadata (for all images)
│   └── tests_common    # acceptance tests applied to all images
│       ├── helpers.py
│       ├── test_notebook.py
│       ├── test_outdated.py
│       ├── test_packages.py
│       └── test_units.py
├── pytest.ini
├── pyvenv.cfg
├── scripts     # All backend scripts. See scripts.md for more details
│   ├── LICENSE.md
│   ├── __init__.py
│   ├── docker_adapter.py
│   ├── fs.py
│   ├── git_helper.py
│   ├── main.py
│   ├── requirements.txt
│   ├── runner.py
│   ├── selenium_setup.sh
│   ├── tagger.py
│   ├── tree.py
│   ├── utils.py
│   └── wiki.py
└── tests   # Tests of all backend scripts (in scripts/). See tests.md for more details and its difference to other tests
    ├── __init__.py
    ├── cred.json
    ├── fake_spec.yml
    ├── test.Dockerfile
    ├── test_resource.zip
    ├── test_docker_adapter.py
    ├── test_runner.py
    ├── test_tree.py
    └── test_wiki.py
```
