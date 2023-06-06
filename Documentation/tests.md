# DataHub Docker Stack: Tests

This document introduces tests in this repo, with focus on the difference of various types of tests.

## Overview

We primarily use `pytest` module to test our code and images. More info can be found about `pytest` [here](https://docs.pytest.org/en/latest/contents.html).

`/pytest.ini` is the configuration file that customizes some pytest behavior. [Official doc](https://docs.pytest.org/en/7.1.x/reference/customize.html) and [this blog](https://subscription.packtpub.com/book/web-development/9781789347562/2/ch02lvl1sec11/configuration-pytest-ini) are good references.

`/images/conftest.py` contains lower-level pytest setup (pytest fixture, if you are interested) code. It's from Jupyter Development Team (3rd party). We don't recommend any change to the file.

## Different Types of Tests

Conceptually, there are two kinds of tests catagorized by their purpose:

- script tests - to ensure the functionality of our backend code. E.g. is the build tree correctly constructed; does the runner stop properly and throw expected error message; etc.
- Image tests - to ensure the functionality of images that we maintain in this repository.

In practice, script tests natually fall in one category, but image tests are further divided into different types according to some other criterias. See below.

## Script Tests

script tests are located in `/tests` and only depends on functions defined in those .py files in `/scripts`.

They are executed locally with `$ pytest tests/test_<module name>.py`.

We highly recommend you write a script test when you create a new module or change an existing module AND run all existing script tests. This is to make sure your change can integrate with existing architectures and save your time before launching and waiting for Github Actions workflow.

Here is a directory structure of the folder:

```bash
tests/
├── __init__.py  # for pytest to work
├── cred.json  # fake credential for testing docker login
├── fake_spec.yml  # works as the spec.yml for test
├── test.Dockerfile   # Dockerfile for testing docker build
├── test_resource.zip  # contains 2 folders that should be put at root dir
├── test_docker_adapter.py
├── test_runner.py
├── test_tree.py
└── test_wiki.py
```

The 4 .py files above are actual test files. They should follow certain structure and naming convention:

- Each .py file in `/scripts` is called a module, so key modules (currently we have 4) should have their own test files.
- The test file name should be `test_<module name>.py`.
- For a module, it's neither required nor recommended to write a test for each function. Some functions are really obvious to be correct; some are local helper functions and thus can be tested along with their callers.
- Each test function should begin with `test_`, e.g. `def test_load_spec():`.
- The part after `test_` should indicate which function in the module it's running test on, but doesn't need to match exactly. Very often, we write separate tests for different cases of a single function. e.g. `test_build_some(self)` and `test_build_all(self)`

## Common Tests

Common tests are located in `/images/tests_common`.

They check against basic container features that MUST hold for EACH image presented in this repo.

Side Note: If an image is based upon **datascience-notebook**, which is the single root in the dependency tree, it's almost guaranteed to pass common tests.

## Image-specific Tests

Image-specific tests are located in `/images/<image_name>/` folder.

Depending on the test scenario and complexity, they are further divided into these categories:

### Basic Tests (REQUIRED)

Location: `/images/<image_name>/test` folder.

Basic tests are automated tests that will be executed during the workflow pipeline, **before** the newly-built image is pushed to Dockerhub.

Relatively simple tests should be put here, and the features they test against should be **internal** to the container. i.e. If something works on your local Docker environment, you are sure it will also work in the production environment (DSMLP).

### Integration Tests

Location: `/images/<image_name>/integration_tests` folder.

Integration tests are also automated tests executed during the workflow pipeline. But as opposed to basic tests, they happen **after** the image push.

Integration tests focus on features **external** to the container. i.e. something that works on your local Docker environment may not work on DSMLP. Here are 2 major contents covered by integration tests.

- network connection: e.g. port number, 404 issue
- UI: e.g. pop-up window, page layout

Currently we only have integration tests for our **rstudio-notebook** image checking against R-Studio UI.

#### **Additional Information on Selenium and Integration-Test Setups

- [Selenium](https://www.selenium.dev/) is a great tool people use to automate tests which involves user actions (open new Tab, click button, etc.) in a Browser.
- [Selenium Webdriver](https://www.selenium.dev/documentation/webdriver/) is the key componet that make Selenium work.
- There are different webdrivers corresponding to different major browsers. We use Google Chrome and its Chrome Driver, which is also the most common choice.
- There is a somehow tricky compatibility issue: Selenium is managed by its own development team, and Chrome Driver is managed by some Google team. Selenium has a great backward-compatibility, meaning it can be driven by any version of Chrome Driver. On the other hand, the compatibility of Chrome broswer and driver is very brittle. In normal case, if the browser major version and driver major version differ by 2 or more, the compatibility breaks. And this doesn't happen rarely. On average, Google Chrome stable advances by 1 major version per month. (By "major version", we mean the 112 in `Version 112.0.5615.137`, for example.)
- We run [this script](/scripts/selenium_setup.sh) during the [main pipeline setup stage](/.github/workflows/main.yml#57) to configure the Github Actions runtime as well as solve the issue above.
- In rare case where you want to add more configuration to the Github Actions runtime, you may add the bash commands directly in
[selenium_setup.sh](/scripts/selenium_setup.sh) or create a new script + a new workflow step (in `main.yml`), depending on whether your change is related to Selenium/Chrome/Driver.

### Manual Tests

Location: `/images/<image_name>/manual_tests` folder.

As the name suggested, they are not included in the automated pipeline. Instead, they are mounted into the image via the Dockerfile, [see](/images/scipy-ml-notebook/Dockerfile#L29).

When you want to test/measure something interactively, when something is too complicated, or when you struggle with getting Selenium automation to work (it happens), you can put them in integration tests.

For example, you can use a .ipynb to train some neural network with tensorflow in real and look at the computation performance in the container. [See](/images/scipy-ml-notebook/manual_tests/tensorflow_mtest.ipynb)

### Workflow Tests

Location: `/images/<image_name>/workflow_tests` folder.

They are a little tricky. Technically, they are "manually triggered automated" tests. This means they will not be included in our automated pipeline (defined by [`main.yml`](/.github/workflows/main.yml)).

Instead, they are defined in separate .yml files in `.github/workflows/`, and manually triggered on Github Actions page. The details of how to create the matching .yml file will be a long discussion and won't be expanded here. [Official doc](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions) is always a good place to start. You can also look at the [existing one](/.github/workflows/test_gpu.yml) we have.

Workflow tests are designed to hold expensive but not-so-important tests. The purpose is to reduce the runtime of the main pipeline by running these tests only when necessary (e.g. before tagging stable images)

Following from that, you can choose to embed the workflow tests inside another workflow. For our **test_gpu** workflow, it's triggered everytime during the **stable tagging** workflow, [workflow definition](/.github/workflows/tag.yml#L17) and [actions.md](/Documentation/actions.md#test_gpuyml).
