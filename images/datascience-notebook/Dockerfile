ARG PYTHON_VERSION=python-3.11.8
FROM quay.io/jupyter/datascience-notebook:$PYTHON_VERSION
# coerce change in all notebooks
USER root

# Setup datascience apt pkgs + env vars
## see https://github.com/phusion/baseimage-docker/issues/319#issuecomment-1058835363
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
    strace \
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

# Jupyter/datahub/nbgrader settup
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

# Python/Mamba Deps
ARG PY_VER_SHORT=3.11
## Package versions
ARG JUPYTERSERVER_VERSION=2.12.5 JUPYTERHUB_VERSION=4.0.2 JUPYTERLAB_VERSION=4.1.2 NBCONVERT_VERSION=7.16.1 NOTEBOOK_VERSION=7.1.1 NBCLASSIC_VERSION=1.0.0
ARG PANDAS_VERSION=2.2.1 STATSMODELS_VERSION=0.14.1

# Install essential+datascience pip packages 
## mistune added for nbgrader issues
RUN pip install pillow typing-extensions tzlocal appdirs gputil mock pytest \
    nltk nltk_data statsmodels==$STATSMODELS_VERSION pandas==$PANDAS_VERSION 'mistune>=2' --upgrade && \
    pip install dpkt nose datascience && \
    python -c 'import matplotlib.pyplot' && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    pip cache purge

# Install jupyterlab+extensions
RUN pip install jupyterhub==$JUPYTERHUB_VERSION jupyter-server==$JUPYTERSERVER_VERSION jupyterlab==$JUPYTERLAB_VERSION notebook==$NOTEBOOK_VERSION nbclassic==$NBCLASSIC_VERSION jupyterlab_rise \
    jupyter_server_terminals jupyter-collaboration jupyterlab-github jupyterlab-latex jupyterlab-git \
    jupyterlab-fasta jupyterlab-pullrequests jupyterlab-geojson jupyterlab-link-share \
    nbconvert==$NBCONVERT_VERSION && \
    pip cache purge

# Install R packages
RUN mamba install -c conda-forge r-markdown r-covr r-git2r r-crosstalk r-dt -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

# Run install-python + cleanup
RUN /usr/share/datahub/scripts/install-python-all.sh && \
    chown -R jovyan:users /opt/conda/etc/jupyter/nbconfig && \
    chmod -R +r /opt/conda/etc/jupyter/nbconfig

# Cleanup
## nbgrader requires some variables set to just run the notebook server
ENV NBGRADER_COURSEID="NA"
ENV JUPYTERHUB_USER=${NB_USER}

RUN pip cache purge
RUN conda clean -t -p -i -y

WORKDIR /home/jovyan
