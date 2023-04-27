# DataHub Docker Stack: Home Page

## Overview

This Github repository builds and maintains the [standard suite of Docker containers](https://support.ucsd.edu/services?id=kb_article_view&sysparm_article=KB0032173&sys_kb_id=e61b198e1b74781048e9cae5604bcbe0) supported by UC San Diego Educational Technology Services.

Currently, we support 4 images:

- datahub-base-notebook (the base notebook all others inherit from)
- datascience-notebook (dpkt + nose + datascience libs)
- scipy-ml-notebook (has PyTorch/Tensorflow + GPU Support)
- rstudio-notebook (installs the RStudio IDE)

## Documentations

To learn more about how each component works, please navigate to its own documentation.

- Table of Contents
  - [Actions](/Documentations/actions.md): how Github Actions help automate our key tasks.
  - [Architecture](/Documentations/architecture.md): the file architecture of this repository and how each components relate to each other.
  - [Images](/Documentations/images.md): what we use and how we use them to maintain our Docker images.
  - [Scripts](/Documentations/scripts.md): how the backend scripts work and what each module does in the bigger picture.
  - [Tests]((/Documentations/tests.md)): how we perform tests and their difference.
  - [Development Guide](/Documentations/dev_guide.md): useful tips to look at and follow if you want to contribute to this repo.
