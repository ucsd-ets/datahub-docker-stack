#!/bin/sh -x
pip install nbgrader==0.6.1

jupyter nbextension install --symlink --sys-prefix --py nbgrader
jupyter nbextension enable --sys-prefix --py nbgrader
jupyter serverextension enable --sys-prefix --py nbgrader

# Disable formgrader for default case, re-enable if instructor
jupyter nbextension disable --sys-prefix formgrader/main --section=tree
jupyter serverextension disable --sys-prefix nbgrader.server_extensions.formgrader
jupyter nbextension disable --sys-prefix create_assignment/main
