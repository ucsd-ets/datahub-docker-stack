# DataHub Docker Stacks Scripts
This readme describes the underlying scripts that build, test, and push our Stack/Wiki.

## Files
* docker_adapter.py
  * A Python wrapper for Docker that helps us run basic Docker commands during our build process.
* fs.py
  * Assists in writing logs during the build.
* git_helper.py
  * A Python wrapper for Git that helps us read information about the commit. This helps us determine which files were changed and subsequently which images need to be updated.
* main.py
  * This file is invoked by [main.yml](/.github/workflows/main.yml) during the workflow and kicks off the build process.
* runner.py
  * This is the main script that performs the image builds along with testing and pushing them to DockerHub by using the rest of the helper scripts in this directory. It also updates our Wiki before it gets pushed by [main.yml](/.github/workflows/main.yml). If you're curious about any one part of the build process and don't know where to start, this file is not a bad place to look.
* tagger.py
  * This handles the [tag.yml](/.github/workflows/tag.yml) workflow that pushes our stable images for production use.
* tree.py
  * This script is a builder for the "Node" object that contain information about each image in our stack, such as image names, parent->child relationships, and whether or not to rebuild the image. It's passed off to the runner.py script to commence the build. It's worth noting that our infrastructure only supports one parent to multiple children builds.
* utils.py
  * Small helper functions that assist with the build.
* wiki.py
  * Contains the code that updates our Wiki and image manifests. See more about our Wiki and what it contains at [architecture.md](/architecture.md).

## The Build Process

After main.py is called from main.yml, main.py does a few things before building the images proper.

* It parses/stores [spec.yml](/images/spec.yml), which contains config information about each image in our stack, including the image names, parent->child relationships, the prefix tag to build the images with (i.e. the '2023.2' in 'ucsdets/scipy-ml-notebook:2023.2-a1230a), and other various info used throughout the build. (@Thomas: Do the build_args overwrite the explicit build args supplied in the Dockerfiles?)
* It detects which images have been changed, which dictates which images will be rebuilt.
  * Currently, a change to the base image (datahub-base-notebook) will trigger a full rebuild on all children, and a change to one child image will rebuild the parent image (so the child has something to inherit from in the build process) but not the siblings.
  * Detection is done on the basis of comparing the current commit pushed and the last commit pushed within the current branch. I.e. if any file was changed in `images/scipy-ml-notebook` in the current commit, but a file wasn't changed in any of the other image subdirs of `images`, the only scipy-ml and the base notebook will be updated.
    * If the action is kicked off by a PR, then it will check for ALL files changed in the PR instead of just the latest commit in the PR.
    * If you put "full rebuild" in your commit message, all of this logic is ignored and all images are rebuilt.
    * If the commit was done to main, a full rebuild is done anyway since these images may go to production.
* It detects the short-hash of the GitHub commit used to kick off the workflow (i.e. a12319). This hash is used to suffix the tags of the images to be pushed.
* It builds the root node that contains information about all of the images to be built and pushed, which is passed off to the runner. Most of this is generated from spec.yml and the changed images.

`build_and_test_containers()` is then called, which generates the success/fail bool of the entire build (as well as doing the build). [You can see the build process at runner.py.](/scripts/runner.py) 

For each node supplied to the function: 
* The corresponding Dockerfile at `images/<image_name>` is run to build an image.
* Tests (both tests that are in `images/<image_name>/tests` and `images/tests_common`) are executed within the Docker container.
* The containers are pushed to DockerHub.
* Integration tests are run (currently only RStudio Selenium tests).
* The Wiki is updated along with corresponding image manifests.

If any of the above steps fail, the build is stopped entirely. Otherwise, the new Wiki is pushed along with the Action's artifacts/logs.

Once the images are up, you're free to use them wherever you like. See [actions.md](/actions.md) for more information about how to deploy the images to production.
