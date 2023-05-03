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

### `build_args`

- They are expected to be used in dynamic image tags for base refs.
- They can also be used for swapping out variables for different plans.
- Can put custom variables in `spec.yml` file.

### Recommended Steps to Follow

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

## Image Update Details

- Every newly pushed images will get a git-hash stamp at the end of the tag
(`ucsdets/datascience-notebook:2021.2-5f71d3b`)
- The `FROM` statement in `Dockerfile` will include `ARG` in the image ref to
support arbitary tags at run-time. This allows for fixating the Dockerfile
while changing the base ref at any time.
- When a dependent images gets its source updated, instead of building the base
image again, only build the dependent image by changing the base ref to the
old remote tag of the image and build from there.
- `stable` tags will be given to the latest built image in each image/plan for
use in production. This process is manually triggered with on Github Action. See [tag.yml](actions.md#tagyml)
