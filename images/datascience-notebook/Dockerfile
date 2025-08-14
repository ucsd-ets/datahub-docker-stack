# If you are building manually, pass PYTHON_VERSION/PY_VER_SHORT/JUPYTERHUB_VERSION with --build-arg 
ARG PYTHON_VERSION=python-3.11.8
ARG PY_VER_SHORT=3.11
ARG JUPYTERHUB_VERSION=4.1.5

# Jupyter has changed where it stores its images
FROM quay.io/jupyter/datascience-notebook:$PYTHON_VERSION
USER root

# Setup datascience apt pkgs + env vars 
## see https://github.com/phusion/baseimage-docker/issues/319#issuecomment-1058835363
ENV DEBIAN_FRONTEND=noninteractive
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
    netcat-openbsd \
    p7zip \
    apt-utils \
    jq \
    build-essential \
    p7zip-full && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    chmod g-s /usr/bin/screen && \
    chmod 1777 /var/run/screen

# Jupyter/datahub/nbgrader setup
COPY /scripts /usr/share/datahub/scripts/
COPY /scripts/jupyter_notebook_config.py /tmp/jupyter_notebook_config_extra.py
COPY /scripts/jupyter_server_config.py /tmp/jupyter_server_config_extra.py
COPY /scripts/nbgrader_config.py /etc/jupyter/nbgrader_config.py
RUN cat /tmp/jupyter_notebook_config_extra.py >> /etc/jupyter/jupyter_notebook_config.py && \
    cat /tmp/jupyter_server_config_extra.py >> /etc/jupyter/jupyter_server_config.py && \
    chmod -R uga+x /usr/share/datahub/scripts/ && \
    chmod -R uga+x /etc/jupyter/jupyter_notebook_config.py && \
    chmod -R uga+x /etc/jupyter/jupyter_server_config.py && \
    chmod -R uga+x /etc/jupyter/nbgrader_config.py

# Copy over R tests to /opt/manual_tests
RUN mkdir /opt/manual_tests
COPY /test/test_r_dump_packages.R /opt/manual_tests
COPY /test/test_r_func.R /opt/manual_tests

# Add additional tests
RUN mkdir -p /opt/workflow_tests
COPY workflow_tests/* /opt/workflow_tests/

USER jovyan

# Python/Mamba Deps
## Package versions
ARG JUPYTERHUB_VERSION=4.1.5 JUPYTERSERVER_VERSION=2.14.2 NBGRADER_VERSION=0.9.3 JUPYTERLAB_VERSION=4.2.4 NBCONVERT_VERSION=7.16.4 NOTEBOOK_VERSION=7.2.1 NBCLASSIC_VERSION=1.1.0
ARG PANDAS_VERSION=2.2.3 STATSMODELS_VERSION=0.14.4 BOTTLENECK_VERSION=1.4.2 NUMEXPR_VERSION=2.10.2

# Install uv for faster package installations
RUN pip3 install --no-cache-dir --upgrade uv

# Install essential+datascience pip packages 
## mistune added for nbgrader issues
RUN uv pip install pillow typing-extensions tzlocal appdirs gputil mock pytest umap-learn --system && \
    uv pip install nltk statsmodels==$STATSMODELS_VERSION pandas==$PANDAS_VERSION mistune --system && \
    uv pip install dpkt nose datascience pyarrow bottleneck==$BOTTLENECK_VERSION umap-learn numexpr==$NUMEXPR_VERSION --system && \
    python -c 'import matplotlib.pyplot' && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    uv cache clean

# Install jupyterlab+extensions
RUN uv pip install jupyterhub==$JUPYTERHUB_VERSION jupyter_server==$JUPYTERSERVER_VERSION --system && \
    uv pip install jupyterlab==$JUPYTERLAB_VERSION notebook==$NOTEBOOK_VERSION nbclassic==$NBCLASSIC_VERSION --system && \
    # (TODO: Re-enable collab once RTC is fixed) uv pip install jupyterlab_rise jupyter_server_terminals jupyter-collaboration --system && \
    uv pip install jupyterlab_rise jupyter_server_terminals --system && \
    uv pip install jupyterlab-latex jupyterlab-git jupyterlab-fasta jupyterlab-geojson --system && \
    uv pip install nbconvert==$NBCONVERT_VERSION nbgrader==$NBGRADER_VERSION --system && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    uv cache clean

# Install R packages
RUN mamba install -c conda-forge r-markdown r-covr r-git2r r-crosstalk r-dt r-sf -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

# Run install-python + cleanup
RUN /usr/share/datahub/scripts/install-python-all.sh && \
    chown -R jovyan:users /opt/conda/etc/jupyter/nbconfig && \
    chmod -R +r /opt/conda/etc/jupyter/nbconfig

# Disable the jupyterlab extensions manager
RUN mamba remove --force sqlite && \
    mamba install -y sqlite && \
    jupyter labextension disable @jupyterlab/extensionmanager-extension

# Cleanup
## nbgrader requires these variables set to just run the notebook server
ENV NBGRADER_COURSEID="NA"
ENV JUPYTERHUB_USER=${NB_USER}

RUN pip cache purge
RUN conda clean -t -p -i -y

WORKDIR /home/jovyan
