# datahub-docker-stack

This Github repository builds and maintains the [standard suite of Docker containers](https://support.ucsd.edu/services?id=kb_article_view&sysparm_article=KB0032173&sys_kb_id=e61b198e1b74781048e9cae5604bcbe0) supported by UC San Diego Educational Technology Services.

Currently, we support 4 images:

* datahub-base-notebook (the base notebook all others inherit from)
* datascience-notebook (dpkt + nose + datascience libs)
* scipy-ml-notebook (has PyTorch/Tensorflow + GPU Support)
* rstudio-notebook (installs the RStudio IDE)

The images are built and pushed to [our organization at DockerHub](https://hub.docker.com/orgs/ucsdets/members) through GitHub Actions. We also use GitHub actions for testing and pushing our stable images to production. [See actions.md](actions.md) for high-level details on how our pipeline works. [You may also check out scripts/README.md](/scripts/README.md) for a more indepth look at the underlying Python code, including logic for which images are run and an overview for how we run tests within the containers.

### Setup virtual environment

Is this necessary? Do you ever run this code locally Thomas?

## Testing the Containers


## Testing /Scripts


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

## Artifacts

Build logs & files can be downloaded after the Github Action completes in an build-artifacts.zip file. Files include:

- logs/<image>.build.log: build logs from docker
- logs/<image>.tests.log: test logs from pytest
- manifests/<image>.md: generated markdown for the wiki
- wiki/*.md: all wiki files that have been updated
