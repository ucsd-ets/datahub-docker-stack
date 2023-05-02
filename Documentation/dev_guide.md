# DataHub Docker Stack: Development Guide

## Docker Concepts

Before listing the commands we use, we'd like to give a brief introduction of Docker concepts.

- **Docker**: Docker is a set of platform as a service (PaaS) products that use OS-level virtualization to deliver software in packages called containers. In short, it's a platform that provide you with containerized/isouldated software/system.
- **Docker Image**: Image is a static, immutable template that defines the behavior of your software/system. Most of the time, we 'build' an image.
- **Docker Container**: Container is a runtime instance. Most of the time, we 'run' or 'start' a container.
- **Dockerhub**: Dockerhub is a place to store your Docker images just like Github stores your code.

## Docker Commands

Here are the commands (signature + example) you will use often:

- image-related

```bash
# Build an image from a local Dockerfile
# <path> is where the Dockerfile stays in
$ docker built -t <image_name>:<tag> <path>
$ docker built -t rstudio-notebook:myTest ./images/rstudio-notebook

# List images
$ docker images

# Pull an image from Dockerhub
$ docker pull <image_name>:<tag>
$ docker pull ucsdets/rstudio-notebook:2023.2-d3e5619

# Push an local image to Dockerhub
$ docker push <image_name>:<tag>
$ docker push ucsdets/rstudio-notebook:2023.2-d3e5619
```

- container-related

```bash
# Run a (new) container
$ docker run -d -p <host port>:<container port> <image_name>:<tag>
$ docker run -d -p 80:80 rstudio-notebook:myTest

# Start a stopped (not active) container
$ docker start <container ID/Name>
$ docker start 87120d0aefb0  # this is container ID

# Stop a running container
$ docker stop <container ID/Name>
$ docker stop 87120d0aefb0  # this is container ID

# List info of all (running or not) containers
$ docker ps -a

# Remove a container
$ docker rm <image_name>:<tag>
$ docker rm rstudio-notebook:myTest
```

Alternatively, you may use [Docker Desktop](https://www.docker.com/products/docker-desktop/) to save you from typing all these commands. But keep in mind that some options are not supported or hard to find in the UI.

[Official Docs](https://docs.docker.com/engine/reference/run/) is the place with most comprehensive information.

If you are familiar with the concepts already, this [cheatsheet](https://dockerlabs.collabnix.com/docker/cheatsheet/) is also a great reference.

## Setup Virtual Environment

If you want to run any Python code from a project locally, it's always a good habit to create a virtual environment and install all required packages there. You can either use conda environment or python venv. They have some subtle difference but are functionally the same for our purpose

```bash
# create a Python venv locally (root of this repo)
$ python -m venv .

# Each time: activate the venv
$ source bin/activate
```

```bash
# create a conda environment
$ conda create --name <name you choose>

# Each time: activate the environment
$ conda activate <name you choose>
```

After you create the virtual environment, install Python packages used in this repo:

```bash
# assume you are in the project root
$ pip install -r scripts/requirements.txt
```

## Adding a New Image

1. Clone the repository and make a new branch: `git checkout -b dev_***_notebook`.
2. Make a new directory under `./images` with the name being the base-name of the new image. For example, for `ucsdets/scipy-ml-notebook`, make a new directory `./images/scipy-ml-notebook`.
3. Modify `./images/spec.yml`. Add a new key under `/images` with the new base-name. Fill in the full `image_name`, its upstream image base-name `depend_on`. To understand what other fields do, please refer to our [images.md](/Documentation/images.md#L20)
4. Under the new directory, add the Dockerfile and the neccessary bits for building the container. For how to write a Dockerfile, please refer to the [official doc](https://docs.docker.com/engine/reference/builder/) or other tutorials.
5. Follow the instructions in [images.md](/Documentation/images.md#recommened-steps-to-follow)

## Modifying an Image (fix bugs or add features)

1. Clone the repository and make a new branch: `$ git checkout -b dev_<image name>`.
2. Under `image/`, find the respective directory for the image you want to change. A manifest of a recent build can be found in the [wiki](https://github.com/ucsd-ets/datahub-docker-stack/wiki) section. An example of a manifest is [here](https://github.com/ucsd-ets/datahub-docker-stack/wiki/ucsdets-datahub-base-notebook-2021.2-ec12f6b).
3. Follow the instructions in [images.md](/Documentation/images.md#recommened-steps-to-follow). This time step #1 should be editing the exisiting Dockerfile.

## Running image tests

1. Activate the virtual environment `$ source bin/activate`
2. `$ cd images`
3. `$ export TEST_IMAGE=MYIMAGE` replace `MYIMAGE` with your locally built image name
4. `$ pytest tests_common` as an example

## Running script tests

Side Note: For `test_wiki.py` to work, please create 3 folders `logs/`, `manifests/`, and `wiki/` under project root. In addition, please copy this [Home_original.md](/tests/Home_original.md) into `wiki/`.

1. Activate the virtual environment `$ source bin/activate`
2. `$ pytest tests/test_<module name>.py` to test a individual module
3. OR `$ pytest tests` to test all modules
