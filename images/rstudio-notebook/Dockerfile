ARG BASE_TAG=latest
FROM ghcr.io/ucsd-ets/datascience-notebook:${BASE_TAG}
#$BASE_TAG
#2021.3-31e0c4e

USER root

# Follow instructions atL https://www.rstudio.com/products/rstudio/download-server/
ENV RSTUDIO_PKG=rstudio-server-2023.09.0-463-amd64.deb
ENV RSTUDIO_URL=https://download2.rstudio.org/server/focal/amd64/${RSTUDIO_PKG}

# rstudio installation expects R to live under /usr/bin, /bin/, etc.
RUN ln -s /opt/conda/bin/R /usr/bin/R && \
    gpg --keyserver keyserver.ubuntu.com --recv-key 8d275962 && \
    apt-get update && \
    apt-get -qq install -y apt-utils gdebi-core dpkg-sig && \
    curl -L ${RSTUDIO_URL} > ${RSTUDIO_PKG} && \
    dpkg-sig --verify ${RSTUDIO_PKG} && \
    gdebi -n ${RSTUDIO_PKG} && \
    rm -f ${RSTUDIO_PKG} && \
    echo '/opt/conda/lib/R/lib' > /etc/ld.so.conf.d/r.conf && /sbin/ldconfig -v && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    rm -f /usr/bin/R && \
    rm /var/lib/rstudio-server/rstudio.sqlite && \
    chmod -R g=u /var/lib/rstudio-server

# Revert to 1.0b6 to correct terminal bug (see https://github.com/jupyterhub/jupyter-rsession-proxy/issues/71)
RUN pip install jupyter-rsession-proxy nbconvert==5.6.1

RUN mkdir -p /etc/rstudio && echo 'auth-minimum-user-id=100' >> /etc/rstudio/rserver.conf

# Rstudio maintains a whitelist of system environment variables made available within an rsession
# make sure our proxy config is included
#RUN ( echo 'http_proxy=${http_proxy-http://web.ucsd.edu:3128}' ; echo 'https_proxy=${https_proxy-http://web.ucsd.edu:3128}' ) >> /opt/conda/lib/R/etc/Renviron.site

# Shim in our nss-wrapper so that user getpwent() lookups succeed
RUN ( echo 'LD_PRELOAD=/opt/k8s-support/lib/libnss_wrapper.so'; echo 'NSS_WRAPPER_PASSWD=/tmp/passwd.wrap'; echo 'NSS_WRAPPER_GROUP=/tmp/group.wrap' ) >> /opt/conda/lib/R/etc/Renviron.site

# The desktop package uses /usr/lib/rstudio/bin
ENV PATH="${PATH}:/usr/lib/rstudio-server/bin" \
    SHELL=/bin/bash \ 
    LD_LIBRARY_PATH="/usr/lib/R/lib:/lib:/usr/lib/x86_64-linux-gnu:/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/amd64/server:/opt/conda/lib/R/lib"

COPY ./lib /opt/k8s-support/lib

RUN R -e "install.packages('rjson', repos='http://cran.rstudio.com/')" && \
    R -e "install.packages('session', repos='http://cran.rstudio.com/')"

COPY ./test ./integration_tests /home/jovyan/
#/usr/share/datahub/tests/datascience-rstudio-docker

USER $NB_USER

RUN conda init bash
