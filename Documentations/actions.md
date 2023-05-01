# DataHub Docker Stack: GitHub Actions

The images are built and pushed to [our organization at DockerHub](https://hub.docker.com/orgs/ucsdets/members) through GitHub Actions. We also use GitHub Actions for testing and pushing our stable images to production. [You may also check out scripts.md](/Documentations/scripts.md) for a more indepth look at the Python code underlying these actions.

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
dump logs and various artifacts that were produced in the Actions run into
zip files and uploaded for reference.

This action defined by `main.yml` triggers our entire pipeline. It happens on all PRs to the main branch and all commits on all branches. (Tips: to skip action on push, add "skip ci" to your commit message.)

### Pipeline Details

A general introduction to `jobs::docker_pipeline` steps in `main.yml`

**Before anything is triggered, Github will check for "skip ci" in PR title and commit message. If the string is found, the entire workflow is skipped.**

**Github runner/runtime** is the top-level caller of the following actions/steps.

- set up the environment by doing general clean-up and dependency installations.
- **`Setup artifacts`**: create subfolders in the project root for storing files.
(`artifacts/`, `manifests/`, `logs/`) See [file system doc](./scripts.md#file-system) for more.
- The pipeline will then look for changes in the `images/` in the latest git
commit determine which images' source was changed and will be used to determine
what images need to be updated. The list of changed images is kept in
`artifacts/IMAGES_CHANGED`.
- **`Clone Wiki`**: clone the `wiki/`, which is a Github backend hidden folder consisting of
`Home.md` and all individual pages of successful image build. The primary purpose is to update
`Home.md` if this is a successful build.
- **`Build stack`**: perform all core tasks of this pipeline which can be broken down into
the following steps [See scripts.md for a more in-depth look at this step.](./scripts.md):
  - use git API to check what files have changed.
  - load information from [spec.yml](../images/spec.yml).
    - This is where all images get their year-quarter prefix from (i.e. 2023.2). It is under tag.prefix.  
  - use above 2 information, build a n-nary tree to encode all details for following tasks.
  - login to DockerHub
  - do a BFS on the tree. For each tree Node (corresponding to an image), a list of operations is carried out. See [scripts.py](scripts.md/#the-build-process)
  - store logs in .yml format to build_artifacts
  - update **the local copy** of `Home.md`; see its function doc
- **`Push Wiki to GitHub`**: (activate ONLY IF **`Build stack`** is successful AND `git.ref`, which is current branch, is main) make the changes to `Home.md` and new image wiki pages permanent and public.
- **`Archive artifacts and logs`**: zip `artifacts/`, `manifests/`, and `logs/` and make it ready
  for download at Actions summary page.

## tag.yml

This action is run manually and requires a given tag that all 4 images have been pushed with at one point (i.e. 2023.2-a1239a). There is an optional dry-run setting that allows you to verify the output of the action without actually pushing new stable images.

After being executed, the action pulls each image in the stack from DockerHub using the ``doit tag`` as defined in [dodo.py](/dodo.py) and then pushes them back up to DockerHub using the format "**ucsdets\<image_name\>:\<year\>.\<quarter\>-stable**". For example: **ucsdets/datascience-notebook:2023.2-stable**.

The tag pulls the year and quarter from the tag on the pre-existing image, regardless of configuration elsewhere. For example, if "2023.2-a1239a" is supplied to the action, it will always return "2023.2-stable" regardless of the current year or quarter.

This action will not run until the test_gpu.yml has been run and passed.

## test_gpu.yml

This action tests code that requires the usage of a GPU on the scipy-ml-notebook. It can be run manually, but will also run everytime tag.yml is called. It takes the same tag argument that tag.yml does.

When executed, the action logs onto dsmlp-login.ucsd.edu as grader-test-01 (who's password is stored in the GitHub Actions secrets, and should be updated if the account's password is to be changed). It then launches the scipy-ml-notebook with the specified tag and runs pytest to verify that Tensorflow and PyTorch work. This test is required to pass for tag.yml to be run.
