# datahub-docker-stack

This Github repository builds and maintains the [standard suite of Docker containers](https://support.ucsd.edu/services?id=kb_article_view&sysparm_article=KB0032173&sys_kb_id=e61b198e1b74781048e9cae5604bcbe0) supported by UC San Diego Educational Technology Services.

## Usage

For students and instructors, check out the offical [FAQ](https://support.ucsd.edu/services?id=kb_article_view&sysparm_article=KB0030470&sys_kb_id=aee8868b1b15f810506f64e8624bcb5e) for running containers on the DSMLP platform.

## Maintenance

For people who are trying to modify the image stack, here are some scenarios and instructions on each.

### Setup virtual environment

```bash
python3 -m venv . # at root level
source bin/activate
which python # it'll point to current dir
which pip # it'll point to current dir
pip install -r scripts/requirements.txt

#!!! IMPORTANT or else imports wont work
export PYTHONPATH=$(pwd)
```

## Run scripts unit tests

```bash
python3 -m unittest tests/v2/test_tester.py

# or
pytest tests/v2/test_<filename>.py
```

## Manually run a module

```bash

# as an example
python scriptss/v2/runner.py

```


### Adding a New Image

1. Clone the repository and make a new branch: `git checkout -b dev_***_notebook`.
2. Make a new directory under `./images` with the name being the base-name of the new image. For example, for `ucsdets/scipy-ml-notebook`, make a new directory `./images/scipy-ml-notebook`.
3. Under the new directory, add the Dockerfile and the neccessary bits for building the container.
4. Modify `./images/spec.yml`. Add a new key under `/images` with the new base-name. Fill in the full `image_name`, its upstream base image key `depend_on`.
5. Push the commit to Github. Make a pull request from the new branch to `main` through the Github interface. Do not merge right now and wait for the workflow ([Github Action](https://github.com/ucsd-ets/datahub-docker-stack/actions)) to finish. It will build the image stack and test each image for features, but it will not push any changes to Dockerhub.
6. If the workflow failed, go to the action details page and debug the issue. Push a new change by amending the first commit `git add . && git commit --amend`.
7. If the workflow completed successfully (a green check to the left of the commit), you can now safely merge the pull request to the `main` branch.
8. The workflow will now run again and push the images to Dockerhub.

### Modifying an Image

1. Clone the repository and make a new branch: `git checkout -b dev_***_notebook`.
2. Under `image/`, find the respective directory for the image you want to change. A manifest of a recent build can be found in the [wiki](https://github.com/ucsd-ets/datahub-docker-stack/wiki) section. An example of a manifest is [here](https://github.com/ucsd-ets/datahub-docker-stack/wiki/ucsdets-datahub-base-notebook-2021.2-ec12f6b).
3. Make the changes and commit to Github. Make a pull request from the new branch to `main` through the Github interface. Do not merge right now and wait for the workflow ([Github Action](https://github.com/ucsd-ets/datahub-docker-stack/actions)) to finish. It will build the image stack and test each image for features, but it will not push any changes to Dockerhub.
4. If the workflow failed, go to the action details page and debug the issue. Push a new change by amending the first commit `git add . && git commit --amend`.
5. If the workflow completed successfully (a green check to the left of the commit), you can now safely merge the pull request to the `main` branch.
6. The workflow will now run again and push the images to Dockerhub.

### Running individual tests for images

1. Activate the virtual environment `source bin/activate`
2. `cd images`
3. `export TEST_IMAGE=MYIMAGE` replace `MYIMAGE` with your locally built image name
4. `pytest tests_common` as an example


### Overview of the Repository
We Use github workflow to builds new images if their is any change in the images or addtional images are added.
.github:-
The main.yml file contains the steps to build the image

Image:- 
- Folder containing the images and each images has its own docker file, test folder for test scripts.
- Spec.yml file is important file where the dependecy of the image and build information specified for an image.

Model:-
- Deprecated

scripts:-
- All code for project
Tests:-
- Contains the test file for testing the submodule
- used with pytest can be called with pytest test_*.py

## Artifacts

Build logs & files can be downloaded after the Github Action completes in an build-artifacts.zip file. Files include:

- logs/<image>.build.log: build logs from docker
- logs/<image>.tests.log: test logs from pytest
- manifests/<image>.md: generated markdown for the wiki
- wiki/*.md: all wiki files that have been updated