ARG PYTHON_VERSION=python-3.8.8
FROM jupyter/datascience-notebook:$PYTHON_VERSION

USER root
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

ARG PY_VER_SHORT=3.8
ARG JUPYTERHUB_VERSION=1.4.2
# nbconvert downgrade needed for nbgrader to work
# jinja downgrade needed to match nbconvert version (imports contextfilter)
RUN /usr/share/datahub/scripts/install-python-all.sh && \
    pip install pandas --upgrade && \
    pip install nltk && \
    pip install nbconvert==5.6.1 && \
    pip install jupyterhub==$JUPYTERHUB_VERSION && \
    pip install nbgrader==0.6.2 && \
    pip install traitlets==5.1.0 && \
    conda install -c conda-forge rise && \
    cat /usr/share/datahub/scripts/canvas_exporter.py > /opt/conda/lib/python$PY_VER_SHORT/site-packages/nbgrader/plugins/export.py && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    chown -R jovyan:users /opt/conda/etc/jupyter/nbconfig && \
    chmod -R +r /opt/conda/etc/jupyter/nbconfig
WORKDIR /home/jovyan

