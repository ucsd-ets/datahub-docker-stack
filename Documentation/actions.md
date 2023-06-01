# DataHub Docker Stack: GitHub Actions

The images are built and pushed to [our organization at DockerHub](https://hub.docker.com/orgs/ucsdets/members) through GitHub Actions. We also use GitHub Actions for testing and pushing our stable images to production. [You may also check out scripts.md](/Documentation/scripts.md) for a more indepth look at the Python code underlying these actions.

We have four actions that we use to develop, test, and deploy our Docker Stack.

- [main.yml](../.github/workflows/main.yml)
  - Build + push + test images.
- [tag.yml](../.github/workflows/tag.yml)
  - Give "stable" tag to production images.
- [tag_global_stable.yml](../.github/workflows/tag_global_stable.yml)
  - Give an extra "global-stable" tag to production images.
- [test_gpu.yml](../.github/workflows/test_gpu.yml)
  - Test GPU code on our scipy-ml-notebook images.

We use a tool called **doit** that allows for more complicated actions to be written and executed during Actions. See [dodo.py for those functions.](/dodo.py)

## main.yml

### AUTO Build and Test CI/CD Pipeline Overview

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
commit to determine which images' source was changed. This information will be used to determine
what images need to be updated. The list of changed images is kept in
`artifacts/IMAGES_CHANGED`.
- **`Clone Wiki`**: clone the `wiki/`, which is a Github backend hidden folder consisting of
`Home.md` and all manifest pages of successful image build. The primary purpose is to add image manifest pages of the current build if we are currently on main.
- **`Build stack`**: perform all core tasks of this pipeline which can be broken down into
the following steps [See scripts.md for a more in-depth look at this step.](./scripts.md):
  - use git API to check what files have changed.
  - load information from [spec.yml](../images/spec.yml).
    - This is where all images get their year-quarter prefix from (i.e. 2023.2). It is under tag.prefix.  
  - use above 2 information, build a n-nary tree to encode all details for following tasks.
  - login to DockerHub
  - do a BFS on the tree. For each tree Node (corresponding to an image), a list of operations is carried out. See [scripts.py](scripts.md/#the-build-process)
  - store logs in .yml format to build_artifacts
- **`Push Wiki to GitHub`**: (activate ONLY IF **`Build stack`** is successful AND `git.ref`, which is current branch, is main) make the new image manifest pages permanent and public.
- **`Archive artifacts and logs`**: zip `artifacts/`, `manifests/`, and `logs/` and make it ready
  for download at Actions summary page.

## tag.yml

This action is run manually and requires an existing tag (most likely 202x.x-main). The requirement is that all 4 images had been pushed to Dockerhub AND their manifests (.md files) exist under wiki, like [this](https://github.com/ucsd-ets/datahub-docker-stack/wiki/ucsdets-scipy-ml-notebook-2023.2-main). There is an optional dry-run setting that allows you to verify the output of the action without actually pushing new stable images.

After being executed, the action pulls each image in the stack from DockerHub using the ``doit tag`` as defined in [dodo.py](/dodo.py) and then pushes them back up to DockerHub using the format "**ucsdets\<image_name\>:\<year\>.\<quarter\>-stable**". For example: **ucsdets/datascience-notebook:2023.2-stable**.

The tag pulls the images with matching tag to the value the user passes in, regardless of configuration elsewhere. For example, if "2021.2-dev" is supplied to the action, it will always try to look for those <image_name>:2021.2-dev and tag them as stable even if the most recent year-quarter prefix is 2023.2.

It will update Home.md by appending the manifest links of these stable images to the table.

This action will not run until the test_gpu.yml has been run and passed.

## tag_global_stable.yml

This is also a manual action and very similar to `tag.yml`. Here are their differences:

- Its purpose is to tag the set of "year-quarter-stable" images (by `tag.yml`) into "global-stable" ones. E.g. **ucsdets/datascience-notebook:2023.2-stable** to **ucsdets/datascience-notebook:stable**.
- A "year-quarter-stable" answers "what are the production images in that quarter", while a "global-stable" answers "what are the production images being used now, this quarter".
- `tag.yml` expect an input like "202x.x-main", but branch name is not necessarily "main". I.e. in rare cases, you may enable the `Push Wiki to GitHub` step for a dev-branch build (such that their markdown manifests exist) and tag them as "year-quarter-stable". But `tag_global_stable.yml` enforces that you can only tag "year-quarter-stable" images into "global-stable".
- The above enforcement is achieved by user input format. `tag.yml` receives **\<year\>.\<quarter\>-<branch_name>**" as input, while `tag_global_stable.yml` only accepts **\<year\>.\<quarter\>**".
- `tag.yml` will update Home.md by appending another cell for "year-quarter-stable" images built in the current tagging action. `tag_global_stable.yml` will rewrite Stable_Tag.md, which only holds a single cell for current global-stable images.

## test_gpu.yml

This action executes code that actually requires the usage of a GPU (that is, training some simple ML model instead of calling `is_gpu_available()` or something) on the scipy-ml-notebook. It can be run manually, but will also run everytime tag.yml is called. It takes the same tag argument that tag.yml does.

When executed, the action logs onto dsmlp-login.ucsd.edu as grader-test-01 (who's password is stored in the GitHub Actions secrets, and should be updated if the account's password is to be changed). It then launches the scipy-ml-notebook with the specified tag and runs pytest to verify that Tensorflow and PyTorch work. This test is required to pass for tag.yml to be run.
