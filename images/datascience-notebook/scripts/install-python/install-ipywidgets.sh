#!/bin/sh -x
pip install --no-cache-dir ipywidgets
	# https://ipywidgets.readthedocs.io/en/7.x/user_install.html
	# According to ^, we don't need this below
	#jupyter nbextension enable --sys-prefix --py widgetsnbextension
