ARG PYTHON_VERSION=python-3.9.5
FROM jupyter/datascience-notebook:$PYTHON_VERSION

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

# VSCode code-server
RUN curl -fsSL https://code-server.dev/install.sh | sh -s -- --prefix=/usr/local

USER jovyan

COPY start-code-server.sh /usr/local/bin/start-notebook.d/

ARG PY_VER_SHORT=3.9
ARG JUPYTERHUB_VERSION=1.5.0
# nbconvert downgrade needed for nbgrader to work
RUN /usr/share/datahub/scripts/install-python-all.sh && \
    pip install pandas --upgrade && \
    pip install nltk \
                jupyterhub==$JUPYTERHUB_VERSION && \
    conda install -c conda-forge rise -y && \
    mamba install -c conda-forge nbgrader -y \
    conda clean --all \
    chown -R jovyan:users /opt/conda/etc/jupyter/nbconfig && \
    chmod -R +r /opt/conda/etc/jupyter/nbconfig

# Install jupyterlab extensions
RUN pip install jupyterlab-github jupyterlab-latex jupyterlab-git \
jupyterlab-fasta jupyterlab-pullrequests jupyterlab-geojson

WORKDIR /home/jovyan
