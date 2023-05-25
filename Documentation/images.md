# DataHub Docker Stack: Images

This document introduces the `images/` folder and the Docker images we maintain in this repository.

## Folder Details

`images/` is a dedicated directory that contains following assets of images in the stack.

- One sub-directory under `images/` equals one unique docker image
- Each sub-directory should/may* contain the following image-specific assets:
  - `Dockerfile`: specify the steps to build the image. See [Docker official doc](https://docs.docker.com/engine/reference/builder/). It should use **build-args** to dynamically point to arbitary base image (see [sample](/images/scipy-ml-notebook/Dockerfile#L1) for details)
  - tests folders: tests specific to this image can be stored under `test/`, `integration_tests/`, `workflow_tests/` and `manual_tests/` depending on their test scenarios. See [tests.md](tests.md) for more details.
  - scripts folders: functionality files (usually in .py) and configuration files (in .sh) to be executed inside the docker container. The common usecase for .sh files is when configuration commands are too many, too long, and contains many environment variables (e.g. `$PATH`). They are mounted to the docker container via Dockerfile `COPY` command.
  - **NOTE**: Above 2 folders are COMPLETELY different from `/scripts` and `/tests` under root level which contains all backend scripts and their respetive tests.
- Folder `tests_common/` contains the pytests for every image. This means any changes to existing images and any new image being added should pass tests here before making permanent.
- File `conftest.py` contains lower-level pytest setup (pytest fixture, if you are interested) code. We don't recommend any change to the file.
- File `change_ignore.json` specify the following 2 things about files and folders inside `/images`:
  - Changes to which files & folders will be ignored when determing what images to rebuild.
  - Changes to which files & folders should always trigger full rebuild (that is, rebuild all images).
- File `spec.yml` contains config information about each image in our stack, including the image names, parent->child relationships, the prefix tag to build the images with (i.e. the '2023.2' in 'ucsdets/scipy-ml-notebook:2023.2-a1230a), and other various info used throughout the build.
  - When a new image is added, this file should be updated accordingly.
  - The image sub-directories created should be equal to the keys under [`images`](/images/spec.yml#L1)
  - Plans can be enabled to serve two or more tracks/versions of the same image
  at the same time under one docker image name. Custom [tag.prefix](/images/spec.yml#L31) are used to
  identify them.
  - `build_args` [like these](/images/spec.yml#L19) overwrite the ones defined in the Dockerfile of that image.
  - `info_cmds` [here](/images/spec.yml#L34) are a way to list out system information about an image. These are
  defined by a name and a corresponding command to run inside the container. Different images can include different sets of info_cmds.

## Image Customization

Things to note when you attempt to add a new image to the repo.

### build args

- Build args are expected to be used in dynamic image tags for base refs.
- They can also be used for swapping out variables for different plans.
- Can put custom variables in `spec.yml` file.

### recommended steps to follow

Please refer to Docker [Official Docs](https://docs.docker.com/engine/reference/run/) and our [development guide](dev_guide.md) for detail usage of commands below.

1. Write a Dockerfile and `$docker build` locally.
2. `$docker run` and enters the container to try out features & functionalities.
3. Read [tests.md](tests.md) to understand how different types of tests works.
4. Add tests you find necessary to corresponding folders.
5. Run these tests locally.
6. Create a new branch and a Pull Request (to merge into main). The PR will automatically trigger the pipeline described in [actions.md](actions.md#pipeline-details)
7. Look at the test logs if any fails and understand the issue.
8. Fix the problem and test locally again. Or, if you found a bug within our `common_tests` (e.g. certain cases are not covered) or our backend scripts in `/scripts`, you are welcome to create a Github Issue.
9. Push your fix. There could be many commits but should be only one push in a single fix attempt. A git push will trigger the pipeline again.
10. Repeat steps 7-9 until the pipeline action passes.

## Image Update Details: About Image Tag

- The usage of a Docker image tag is very similar to the branch in a Github repo. Some common tag choices
are "stable", "latest", "beta", "dev", etc.
- And very naturally, we use the branch name and combine it with the "year.quarter" prefix to form our Docker image tag. A tag in this form gives us developers a clear idea of the time and purpose of a group of images. For example, `ucsdets/datascience-notebook:2021.2-update_pytorch`.
- At the same time, we save the pain from finer-grained tag/identifier aiming to give a unique tag to each image we previously built. 99% of the time, there is a 1-1 correspondence between a branch and a feature/debug update, and we need multiple build attempts before making things work. Thus, it's unnecessary to distinguish between images under the same branch.
- The `FROM` statement in `Dockerfile` will include `ARG` in the image ref to
support arbitary tags at run-time. This allows for fixating the Dockerfile
while constructing a "year.quater-<branch_name>" tag as `ARG` at run time.
- When a child image gets its source updated, instead of building the base/parent
image again, we only build the child image, if on the same branch, because the tag remains the same.
- `stable` tags will be given to the latest-built production-ready image in each image/plan for
usage. This process is manually triggered with on Github Action. See [tag.yml](actions.md#tagyml)

## Image Build Cache

Cache is critical in terms of build efficiency. Based on our experiment, doing a full rebuild from scratch takes around 50 mins, while a rebuild utilizing cache takes only 15 mins.

**What is Cache?**

In docker, cache can be loosely defined as "image layers that already exist in your storage". Docker image is composed of layers, each corresponding to one command in the Dockerfile. To have a better idea, you may fetch a Dockerfile (better non-trivial) to your current dir and try the following:

1. `$docker build -t test_img:fresh .` (The . is part of the command saying the Dockerfile is in the current dir) You will find each `STEP` like installation is actually carried out and will take some time.
2. `$docker build -t test_img:repeat .` We build again without changing the Dockerfile at all. This time you will find the build process finishes instantly, because each `STEP` is `CACHED`.
3. Add some trivial command, like `RUN echo "Hello"` at the second last step, then run `$docker build -t test_img:new_step .` You will find that all commands before your new command still utilize cache, but the last command which comes after the new one does not.

**Local or Remote Cache?**

When building images locally, Docker will automatically utilize the cached layers, because those layers are presented somewhere in the local storage. But this doesn't hold for Github Actions, because after each action run, our runtime environment will be deallocated and the next run will start from a new environment.

There is a "local" solution, which is leveraging the [`Caches Management` provided by Github](https://github.com/ucsd-ets/datahub-docker-stack/actions/caches). The problem is cache stroage there is limited to 5GB and this is much lower than our need.

Another choice, or a workaround, is to use "remote" cache. This means we `docker pull` the image beforehand such that `docker build` can utilize the cache. This is less efficient than local cache, and may be worse than not using cache if download is slow. We use this approach, because the download bandwidth offered by Github is good and the time we spend on pulling/downloading is a lot shorter than no-cache build time.

**Logic: what to do in different cache scenarios of an image?**

In each action run, for each image, we always perform a [Dockerhub-existence check](/scripts/docker_adapter.py#L299). This is a very cheap `$docker manifest inspect` command. It will check whether the same image with the same tag (the branch name) is presented on Dockerhub. This is the best-choice cache.

1. If it's there, but `node.rebuild` is false, we won't bother pulling the image.
2. If it's there, and `node.rebuild` is true, we pull the image and use it as cache later.
3. If it's not there, we mark `node.rebuild` to true even if it's false, because this "unnecessary" rebuild will provide cache and save build time in future runs. Then we pull the stable image `<node.image_name>:stable` and use it as cache later. This is the sub-optimal cache choice because the image definition on a dev branch can be quite different from the current stable definition, and thus not many layers are cached.
