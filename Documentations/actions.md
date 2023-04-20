# DataHub Docker Stack: GitHub Actions (TODO)

We have three main actions that we use to develop, test, and deploy our Docker Stack.

- [main.yml](../.github/workflows/main.yml)
  - Build + push + test images.
- [tag.yml](../.github/workflows/tag.yml)
  - Give images the "stable" tag that we use for production images.
- [test_gpu.yml](../.github/workflows/test_gpu.yml)
  - Test GPU code on our scipy-ml-notebook images.

We use a tool called **doit** that allows for more complicated actions to be written and executed during Actions. See [dodo.py for those functions.](/dodo.py)

## main.yml

### CI/CD Pipeline Overview

Updating Docker images is very similar to updating an open-source library.
Build, test, and deploy will be building the Docker images, testing images if
they have the right contents and features, and lastly publishing it on
Dockerhub. We also add in steps to generate image "manifests" for listing out
package informations and publishing them to the project wiki, and steps to
dump logs and various artifacts that were produced in the Action run into
zip files and uploaded for reference.

This action define by `main.yml` kicks off our entire pipeline. It happens on all PRs to the main branch and all commits on all branches.

### Pipeline Details

(TODO: UPDATE below steps)

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

First, it cleans the environment up in the GitHub runner (removing vestigial files and making sure the docker environment is clean) to save space. It then installs relevant dependencies (Python + some libs, Selenium, pydoit). It then checks out the wiki and runs `python3 scripts/main.py`, which kicks off the Python code that updates our wiki + builds, tests, and pushes the Docker stack. [See scripts.md for a more indepth look at our pipeline.](./scripts.md)

After the Python code exits successfully, the updated Wiki is pushed to GitHub as well as some logs that are attached to the Action as build artifacts.

## tag.yml

This action is run manually and requires a given tag that all 4 images have been pushed with at one point (i.e. 2023.2-a1239a). There is an optional dry-run setting that allows you to verify the output of the action without actually pushing new stable images.

After being executed, the action pulls each image in the stack from DockerHub using the ``doit tag`` as defined in [dodo.py](/dodo.py) and then pushes them back up to DockerHub using the format "**ucsdets\<image_name\>:\<year\>.\<quarter\>-stable**". For example: **ucsdets/datascience-notebook:2023.2-stable**.

The tag pulls the year and quarter from the tag on the pre-existing image, regardless of configuration elsewhere. For example, if "2023.2-a1239a" is supplied to the action, it will always return "2023.2-stable" regardless of the current year or quarter.

This action will not run until the test_gpu.yml has been run and passed.

## test_gpu.yml

This action tests code that requires the usage of a GPU on the scipy-ml-notebook. It can be run manually, but will also run everytime tag.yml is called. It takes the same tag argument that tag.yml does.

When executed, the action logs onto dsmlp-login.ucsd.edu as grader-test-01 (who's password is stored in the GitHub Actions secrets, and should be updated if the account's password is to be changed). It then launches the scipy-ml-notebook with the specified tag and runs pytest to verify that Tensorflow and PyTorch work. This test is required to pass for tag.yml to be run.
