ARG PYTHON_VERSION=python-3.9.5
FROM jupyter/datascience-notebook:$PYTHON_VERSION
# coerce change in all notebook
USER root

# see https://github.com/phusion/baseimage-docker/issues/319#issuecomment-1058835363
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NOWARNINGS="yes"

RUN apt-get update -y && \
    apt-get -qq install -y --no-install-recommends \
    git \
    curl \
    rsync \
    unzip \
    less \
    nano \
    vim \
    cmake \
    tmux \
    screen \
    gnupg \
    htop \
    wget \
    openssh-client \
    openssh-server \
    p7zip \
    apt-utils \
    jq \
    build-essential \
    p7zip-full && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    chmod g-s /usr/bin/screen && \
    chmod 1777 /var/run/screen

COPY /scripts /usr/share/datahub/scripts/
COPY /scripts/jupyter_notebook_config.py /tmp/jupyter_notebook_config_extra.py
COPY /scripts/nbgrader_config.py /etc/jupyter/nbgrader_config.py
RUN cat /tmp/jupyter_notebook_config_extra.py >> /etc/jupyter/jupyter_notebook_config.py && \
    chmod -R uga+x /usr/share/datahub/scripts/ && \
    chmod -R uga+x /etc/jupyter/jupyter_notebook_config.py && \
    chmod -R uga+x /etc/jupyter/nbgrader_config.py

# Copy over R tests to /opt/manual_tests
RUN mkdir /opt/manual_tests
COPY /test/test_r_dump_packages.R /opt/manual_tests
COPY /test/test_r_func.R /opt/manual_tests

USER jovyan

ARG PY_VER_SHORT=3.9
ARG JUPYTERHUB_VERSION=3.0.0

# mistune added for nbgrader issues

# coerce pandas to 1.5.3. 2.0 released april 3rd and currently breaks tests.
RUN /usr/share/datahub/scripts/install-python-all.sh && \
    pip install pandas==2.0.3 'mistune>=2' --upgrade && \
    pip install nltk \
    pip install statsmodels==0.14.0 \
    nbconvert==7.2.1 \
    jupyterhub==$JUPYTERHUB_VERSION && \
    mamba install -c conda-forge rise -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    conda clean --all && \
    chown -R jovyan:users /opt/conda/etc/jupyter/nbconfig && \
    chmod -R +r /opt/conda/etc/jupyter/nbconfig

# nbgrader requires some variables set to just run the notebook server
ENV NBGRADER_COURSEID="NA"
ENV JUPYTERHUB_USER=${NB_USER}

# Install jupyterlab extensions
RUN pip install jupyterlab==3.0.16 jupyterlab-github jupyterlab-latex jupyterlab-git \
    jupyterlab-fasta jupyterlab-pullrequests jupyterlab-geojson

# Datascience packages
RUN pip install dpkt \
    nose \
    datascience && \
    python -c 'import matplotlib.pyplot' && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

RUN conda clean -tipsy

# ENV SHELL=/bin/bash Weird, this line is in the datascience and rstudio notebooks but not scipyml

WORKDIR /home/jovyan
