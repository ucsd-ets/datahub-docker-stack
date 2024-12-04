ARG BASE_TAG=latest
FROM ghcr.io/ucsd-ets/datascience-notebook:${BASE_TAG}

USER root

# RStudio Setup

# Ubuntu 22 setup with v 2024.04.2-764
## Follow instructions at https://www.rstudio.com/products/rstudio/download-server/
ENV RSTUDIO_PKG=rstudio-server-2024.09.1-394-amd64.deb
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
# When we upgraded to Python3.11/JLab 4 upstreamed from Jupyter, our distro was also upgraded from Ubuntu 20 to 22. 
# This introduced a new issue where RStudio would prefer /opt/conda/lib's OpenSSL instead of /usr/lib when trying to download packages using internet.so (internal RStudio lib).
# https://github.com/rstudio/rstudio/issues/14060 - the fix described was setting LD_LIBRARY_PATH to /opt/conda/lib:/usr/lib/x86_64-linux-gnu (globally or just for RStudio).
# However, this fix is problematic because many executables such as SSH*/git rely on the OpenSSL version being installed by apt (since they are installed by apt).
# Post-fix, when you tried to launch ssh/git in the RStudio Termina, you would receieve an "OpenSSL mismatch" error.
# To fix this, we simply added a bash wrapper for all affected binaries that forces them to always use the correct LD_LIBRARY_PATH (apt). 
# If another binary encounters a "OpenSSL mismatch error," add it here.
# Hopefully a better fix can be found - the core issue here seems to be conda and its obtrusiveness

# List of binaries you want to wrap
ENV FORCED_BINARIES="ssh ssh-add ssh-agent ssh-copy-id ssh-keygen ssh-keyscan sshd git"

# Loop over each binary and apply the wrapper
RUN for bin in $FORCED_BINARIES; do \
      if [ -f /usr/bin/$bin ]; then \
        mv /usr/bin/$bin /usr/bin/$bin.orig && \
        echo '#!/bin/bash' > /usr/bin/$bin && \
        echo 'export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu' >> /usr/bin/$bin && \
        echo 'exec /usr/bin/'$bin'.orig "$@"' >> /usr/bin/$bin && \
        chmod +x /usr/bin/$bin; \
      fi; \
    done

COPY ./lib /opt/k8s-support/lib

COPY ./test ./integration_tests /home/jovyan/

RUN chmod 777 /var/ -R

USER $NB_USER

# Cleanup
RUN conda init bash
