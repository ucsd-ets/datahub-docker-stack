ARG BASE_TAG=latest
FROM ucsdets/datahub-base-notebook:$BASE_TAG

USER jovyan

RUN pip install dpkt \
                nose \
                datascience && \
    python -c 'import matplotlib.pyplot' && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

RUN conda clean -tipsy

ENV SHELL=/bin/bash


