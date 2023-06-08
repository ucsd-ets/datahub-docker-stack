# DataHub Docker Stacks: Scripts

This document describes the underlying scripts that build, test, and push our docker image stack and update our Github Wiki page.

## .py Files

**The following scripts are used by our current workflows and are likely used in future ones we add.**

- utils.py
  - Small helper functions that assist with the build.
- fs.py
  - Assists in writing logs during the build and test.
  - Currently used for storing [build-artifacts](#3-postwork-archive-build-artifacts)
- git_helper.py
  - A Python wrapper for Git that helps us read information about the commit.
  - It helps us determine which files were changed and subsequently which images need to be updated.
  - It also retrieves the shortened hash of the most recent git commit which, under current implementation, is used as part of the image tag.
- tree.py
  - This script defines a [`Node`](/scripts/tree.py#L8) object that contain information about each image in our stack, such as image names, parent->child relationships, and whether or not to rebuild the image.
  - It also defines a key helper function [`build_tree()`](/scripts/tree.py#L59). The function utilizes static information from [spec.yml](/images/spec.yml) and dynamic information "which images have been changed" to build a tree according to image dependencies.
  - The root node is then passed off to the runner.py script to commence the build.
  - The tree structure is chosen because it matches Docker image dependency (each image can be `FROM` only one base image) and doesn't require extra work when the level of dependencies increases. (Currently it's single-level.)
  - It's worth noting that our infrastructure only supports one parent to multiple children builds. But potentially it can be generalized with only some minor change: create a dummy node and group every root together.
- docker_adapter.py
  - A Python wrapper for Docker that helps us run basic Docker commands during our build process.
  - It serves as an interface between Python Docker SDK and our Docker client.
  - `try-except` block has been placed around docker commands. The logger will print more readable and informative information upon an Docker error.

**The following scripts are specific to our [main.yml](/.github/workflows/main.yml) workflow.**

- runner.py
  - This is the main script that performs the image builds along with testing and pushing them to DockerHub by using the rest of the helper scripts in this directory. It also updates our **local** Wiki before it gets pushed by **`Push Wiki to GitHub`**. If you're curious about any one part of the build process and don't know where to start, this file is not a bad place to look.
- main.py
  - This file is the top-level caller invoked by [main.yml](/.github/workflows/main.yml) during the workflow and launches the entire process.

**These scripts are specific to our [tag.yml](/.github/workflows/tag.yml) workflow.**

- wiki.py
  - Contains the code that updates our Wiki.
  - By "Wiki", we refer to the hidden `wiki/` folder managed by Github, which renders Wiki pages.
  - Wiki of this repo contains a `Home.md`, a `Stable_Tag.md`, and individual .md files for each image currently or previously in use.
  - We will call those individual .md files "(image) manifests".
  - NOTE: manifests are created locally in Github Actions runtime, stored to build-arfiacts, but will not be found in the Github Wiki pages unless under certain conditions. See **`Push Wiki to GitHub`** step in [actions.md](actions.md)
- tagger.py
  - It doesn't build new images but pulls existing images and gives them an extra "stable" tag.
  - It pushes our stable images for production use and updates [Stable_Tag.md](https://github.com/ucsd-ets/datahub-docker-stack/wiki/Stable_Tag) or [Home.md](https://github.com/ucsd-ets/datahub-docker-stack/wiki), depending on which tagging action is called. See [action.md](/Documentation/actions.md#tag_global_stableyml)

## The Build Process

**This section aims to explain the `Build stack` step outlined in [action.md](./actions.md/#pipeline-details) with more implementation details.**  
**The function being called will be placed at the end of the bullet (step). For finer-grained details of any particular function, please check its doc-string**

After `python3 main.py` is called from main.yml, it does a few things to ensure the entire build process is correct, successful, and its outcomes (images + Wiki) ready for production or debug. See [main.main()](/scripts/main.py#L15)

### 1. Prework: Setup the `build-info` Tree

- It parses and stores static information defined in [spec.yml](/images/spec.yml). For more details, see [images.md](./images.md/#image-stack-details) for what information it contains. [`load_spec()`](/scripts/tree.py#L41)
- It detects which files have been changed, which dictates which images will be rebuilt. [`get_changed_images()`](scripts/git_helper.py#L44)
  - Currently, a change to the base image (datascience-notebook) will trigger a full rebuild on all children, and a change to one child image will rebuild the parent image (so the child has something to inherit from in the build process) but not the siblings.
  - Detection is done on the basis of comparing the current commit pushed and the last commit pushed within the current branch. I.e. if any file was changed in `images/scipy-ml-notebook` in the current commit, but a file wasn't changed in any of the other image subdirs of `images`, the only scipy-ml and the base notebook will be updated. But there are some extra rules:
    - If the action is triggered by a PR, then it will check for ALL files changed in the PR instead of just the latest commit in the PR.
    - If you put "full rebuild" in your commit message, all of this logic is ignored and all images are rebuilt.
    - If this is the first Github Actions run of the current branch, all images are rebuilt.
    - If the commit was done to main, a full rebuild is done anyway since these images may go to production.
- This current branch name is used to suffix the tags of the images to be pushed. [`get_branch_name()`](/scripts/git_helper.py#L35)
- It constructs the root node that contains information about all of the images to be built and pushed, which is passed off to the runner. [`build_tree()`](/scripts/tree.py#L59)

### 2. Core: [`build_and_test_containers()`](/scripts/runner.py#L130)

- It logs into the Docker client of Python SDK with Github secrets **DOCKERHUB_TOKEN** and **DOCKERHUB_USER**. [`login()`](/scripts/docker_adapter.py#L86)
- It also logs into the Docker daemon directly using `docker login` CLI. This enables the checking of existence of an image with a particular tag on Dockerhub, see [build cache explanation](/Documentation/images.md#image-build-cache) and [its implementation](/scripts/docker_adapter.py#L315) for more details.
- It performs a BFS on the build-info tree and does the following to each Node if isn't marked skipped:
  - build: The corresponding Dockerfile at `images/<image_name>` is run to build an image. [`build()`](/scripts/docker_adapter.py#L31)
  - basic test: Image-specific tests in `images/<image_name>/tests/` and common tests (apply to all images) in `images/tests_common/` are executed within the Docker container. [`run_basic_test()`](/scripts/runner.py#L94)
  - push: The containers are pushed to DockerHub. [`push()`](/scripts/docker_adapter.py#L104)
  - integration test: More complicated tests in `images/<image_name>/integration_tests/` are exececuted to ensure it works in our production environment. (currently only RStudio Selenium tests) [`run_integration_tests()`](/scripts/runner.py#L111)
  - create manifests: some informative commands (like `pip list`) defined in [spec.yml](/images/spec.yml) are executed, and their console outputs are written to a formatted .md file for each individual image. [`write_report()`](/scripts/wiki.py#L127)
  - reclaim space: Clean Docker cache of steps above. **Executed when .prune is set to true in spec.yml**. [`prune()`](/scripts/docker_adapter.py#L190)
- If any of the above steps fail, subsequent images will not be checked. We break from the loop and move to the Postwork below.
- But as long as steps of an image start, a [`Result`](/scripts/runner.py#L22) is created to store the results of each step.

### 3. Postwork: archive `build-artifacts`

- Useful information of each image from previous section is all stored in [`Result`](/scripts/runner.py#L22). It will be parsed to strings and written to the following directories:
- `artifacts/`: it contains the [`Result`](/scripts/runner.py#L22) turned into a .yml file for each "started" image.
- `logs/`: it contains various types of logs that may help with debug
  - a `run.log` which is the same as what we see in the Github Actions page.
  - a `<image_fullname>.build.log` which is the console output during `docker build` of each image.
  - a `<image_fullname>.basic-tests.log` which is the pytest output of basic test of each image.
  - ALL other useful debugging information of ALL file formats can and should be stored here. E.g. screenshots by Selenium upon test failure.
- `manifests`: it contains the manifest (.md file) for each successful image of this build.
