ARG BASE_TAG=latest
FROM ghcr.io/ucsd-ets/datascience-notebook:${BASE_TAG}

USER root

# RStudio Setup

# Ubuntu 22 setup with v 2024.04.2-764
## Follow instructions at https://www.rstudio.com/products/rstudio/download-server/
ENV RSTUDIO_PKG=rstudio-server-2024.04.2-764-amd64.deb
ENV RSTUDIO_URL=https://download2.rstudio.org/server/jammy/amd64/${RSTUDIO_PKG}

## rstudio installation expects R to live in /usr/bin, /bin/, etc.
RUN ln -s /opt/conda/bin/R /usr/bin/R && \
    apt-get update && \
    apt-get -qq install -y apt-utils gdebi-core dpkg-sig && \
    wget ${RSTUDIO_URL} && \
    gdebi -n ${RSTUDIO_PKG} && \
    rm -f ${RSTUDIO_PKG} && \
    echo '/opt/conda/lib/R/lib' > /etc/ld.so.conf.d/r.conf && /sbin/ldconfig -v && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    rm -f /usr/bin/R && \
    chmod -R g=u /var/lib/rstudio-server && \
    service rstudio-server restart

RUN pip install jupyter-rsession-proxy

RUN mkdir -p /etc/rstudio && \
    echo 'auth-minimum-user-id=100' >> /etc/rstudio/rserver.conf

## Shim in our nss-wrapper so that user getpwent() lookups succeed
RUN ( echo 'LD_PRELOAD=/opt/k8s-support/lib/libnss_wrapper.so'; echo 'NSS_WRAPPER_PASSWD=/tmp/passwd.wrap'; echo 'NSS_WRAPPER_GROUP=/tmp/group.wrap') >> /opt/conda/lib/R/etc/Renviron.site

## The desktop package uses /usr/lib/rstudio/bin
ENV PATH="${PATH}:/usr/lib/rstudio-server/bin" \
    SHELL=/bin/bash \
    LD_LIBRARY_PATH="/opt/conda/lib:/usr/lib/x86_64-linux-gnu"

### OpenSSL Conda Workarounds
# ssh-keygen
RUN mv /usr/bin/ssh-keygen /usr/bin/ssh-keygen.orig
RUN echo '#!/bin/bash' > /usr/bin/ssh-keygen && \
    echo 'export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu' >> /usr/bin/ssh-keygen && \
    echo 'exec /usr/bin/ssh-keygen.orig "$@"' >> /usr/bin/ssh-keygen && \
    chmod +x /usr/bin/ssh-keygen

# git
RUN mv /usr/bin/git /usr/bin/git.orig
RUN echo '#!/bin/bash' > /usr/bin/git && \
    echo 'export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu' >> /usr/bin/git && \
    echo 'exec /usr/bin/git.orig "$@"' >> /usr/bin/git && \
    chmod +x /usr/bin/git

# ssh
RUN mv /usr/bin/ssh /usr/bin/ssh.orig
RUN echo '#!/bin/bash' > /usr/bin/ssh && \
    echo 'export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu' >> /usr/bin/ssh && \
    echo 'exec /usr/bin/ssh.orig "$@"' >> /usr/bin/ssh && \
    chmod +x /usr/bin/ssh

COPY ./lib /opt/k8s-support/lib

COPY ./test ./integration_tests /home/jovyan/

RUN chmod 777 /var/ -R

USER $NB_USER

# Cleanup
RUN conda init bash
