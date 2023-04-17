# DataHub Docker Stack GitHub Actions

We have three main actions that we use to develop, test, and deploy our Docker Stack.

* [main.yml](.github/workflows/main.yml)
  * Build + push + test images.
* [tag.yml](.github/workflows/tag.yml)
  * Give images the "stable" tag that we use for production images.
* [test_gpu.yml](.github/workflows/test_gpu.yml)
  * Test GPU code on our scipy-ml-notebook images.

We use a tool called **doit** that allows for more complicated actions to be written and executed during Actions. See [dodo.py for those functions.](/dodo.py)

## main.yml
This action kicks off our entire pipeline. It happens on all PRs to the main branch and all commits on all branches.

First, it cleans the environment up in the GitHub runner (removing vestigial files and making sure the docker environment is clean) to save space. It then installs relevant dependencies (Python + some libs, Selenium, pydoit). It then checks out the wiki and runs `python3 scripts/main.py`, which kicks off the Python code that updates our wiki + builds, tests, and pushes the Docker stack. [See /scripts for a more indepth look at our pipeline.](/scripts/README.md)

After the Python code exits successfully, the updated Wiki is pushed to GitHub as well as some logs that are attached to the Action as build artifacts.

## tag.yml
This action is run manually and requires a given tag that all 4 images have been pushed with at one point (i.e. 2023.2-a1239a). There is an optional dry-run setting that allows you to verify the output of the action without actually pushing new stable images.

After being executed, the action pulls each image in the stack from DockerHub using the ``doit tag`` as defined in [dodo.py](/dodo.py) and then pushes them back up to DockerHub using the format "**ucsdets\<image_name\>:\<year\>.\<quarter\>-stable**". For example: **ucsdets/datascience-notebook:2023.2-stable**.

The tag pulls the year and quarter from the tag on the pre-existing image, regardless of configuration elsewhere. For example, if "2023.2-a1239a" is supplied to the action, it will always return "2023.2-stable" regardless of the current year or quarter.

This action will not run until the test_gpu.yml has been run and passed.

## test_gpu.yml
This action tests code that requires the usage of a GPU on the scipy-ml-notebook. It can be run manually, but will also run everytime tag.yml is called. It takes the same tag argument that tag.yml does.

When executed, the action logs onto dsmlp-login.ucsd.edu as grader-test-01 (who's password is stored in the GitHub Actions secrets, and should be updated if the account's password is to be changed). It then launches the scipy-ml-notebook with the specified tag and runs pytest to verify that Tensorflow and PyTorch work. This test is required to pass for tag.yml to be run.

