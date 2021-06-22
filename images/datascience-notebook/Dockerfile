FROM ucsdets/datahub-base-notebook:2021.1-stable

LABEL MAINTAINER="UC San Diego ITS/ETS-EdTech-Ecosystems <acms-compinf@ucsd.edu>"

# Install OKpy for DSC courses
# downgrade pip temporarily and upgrade to fix issue with okpy install
USER root
RUN pip install --upgrade --force-reinstall pip==9.0.3
RUN pip install okpy --disable-pip-version-check
RUN pip install --upgrade pip

RUN pip install dpkt \
                nose \
                datascience

# Pregenerate matplotlib cache
RUN python -c 'import matplotlib.pyplot'

RUN conda clean -tipsy

# import integration tests
ENV TESTDIR=/usr/share/datahub/tests
ARG DATASCIENCE_TESTDIR=${TESTDIR}/datascience-notebook
COPY tests ${DATASCIENCE_TESTDIR}
RUN chmod -R +rwx ${DATASCIENCE_TESTDIR}
RUN chown 1000:1000 ${DATASCIENCE_TESTDIR}

# change the owner back
RUN chown -R 1000:1000 /home/jovyan
USER $NB_UID
ENV SHELL=/bin/bash
