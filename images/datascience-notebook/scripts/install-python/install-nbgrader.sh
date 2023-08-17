#!/bin/bash

pip install nbgrader==0.8.4

jupyter nbextension install --symlink --sys-prefix --py nbgrader
jupyter nbextension enable --sys-prefix --py nbgrader
jupyter serverextension enable --sys-prefix --py nbgrader

jupyter labextension enable --level=system nbgrader
jupyter server extension enable --system --py nbgrader
