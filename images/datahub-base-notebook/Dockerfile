ARG PYTHON_VERSION=python-3.9.5
FROM jupyter/datascience-notebook:$PYTHON_VERSION
#
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

# mistune added for nbgrader issues

# coerce pandas to 1.5.3. 2.0 released april 3rd and currently breaks tests.
RUN /usr/share/datahub/scripts/install-python-all.sh && \
    pip install pandas==1.5.3 'mistune>=2' --upgrade && \
    pip install nltk \
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
RUN pip install jupyterlab-github jupyterlab-latex jupyterlab-git \
jupyterlab-fasta jupyterlab-pullrequests jupyterlab-geojson

WORKDIR /home/jovyan
