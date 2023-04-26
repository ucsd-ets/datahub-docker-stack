# DataHub Docker Stack: Tests (TODO)

This document introduces tests in this repo, with focus on the difference of various types of tests.

## Overview

We test our code and images using `pytest` module. More info can be found [here](https://docs.pytest.org/en/latest/contents.html).

`/pytest.ini` is the configuration file that customizes some pytest behavior. [Official doc](https://docs.pytest.org/en/7.1.x/reference/customize.html) and [this blog](https://subscription.packtpub.com/book/web-development/9781789347562/2/ch02lvl1sec11/configuration-pytest-ini) are good references.

`/images/conftest.py` contains lower-level pytest setup (pytest fixture, if you are interested) code. It's from Jupyter Development Team (3rd party). We don't recommend any change to the file.

## Different Types of Tests

Conceptually, there are two kinds of tests catagorized by their purpose:

- script tests - to ensure the functionality of our backend code. E.g. is the build tree correctly constructed; does the runner stop properly and throw expected error message; etc.
- Image tests - to ensure the functionality of images that we maintain in this repository.

In practice, script tests natually fall in one category, but image tests are further divided into different types according to some other criterias. See below.

### script tests

script tests are located in `/tests` and only depends on functions defined in those .py files in `/scripts`.

It should be

We also have a way to easily run arbitrary python files in a container.
This is useful for running unit tests of packages we use, so we put these files in `{image}/test/units` folder.
An example of such a test is [unit_pandas.py](https://github.com/jupyter/docker-stacks/blob/master/scipy-notebook/test/units/unit_pandas.py).
