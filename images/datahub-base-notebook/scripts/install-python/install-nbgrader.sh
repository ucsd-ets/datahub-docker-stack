#!/bin/bash

pip install nbgrader==0.8.1

jupyter labextension enable --level=system nbgrader
jupyter server extension enable --system --py nbgrader