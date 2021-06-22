FROM jupyter/datascience-notebook:python-3.8.6

USER root

COPY /scripts /usr/share/datahub/scripts/
COPY /scripts/run_jupyter.sh /
COPY /scripts/jupyter_notebook_config.py /etc/jupyter/jupyter_notebook_config.py


# nbconvert downgrade needed for nbgrader to work
RUN /usr/share/datahub/scripts/install-all.sh && \
	pip install pandas --upgrade && \
	pip install nltk && \
    pip install nbconvert==5.6.1 && \
	cat /usr/share/datahub/scripts/canvas_exporter.py > /opt/conda/lib/python3.8/site-packages/nbgrader/plugins/export.py && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    chown -R jovyan:users /opt/conda/etc/jupyter/nbconfig && \
    chmod -R +r /opt/conda/etc/jupyter/nbconfig

# make compatible with DSMLP version of jupyterhub
RUN pip install jupyterhub==0.9.2

# testing directory
COPY /tests /usr/share/datahub/tests/datahub-base-notebook
RUN chown -R 1000:1000 /usr/share/datahub/tests/datahub-base-notebook && \
    chmod -R +rwx /usr/share/datahub/tests/datahub-base-notebook

USER jovyan
WORKDIR /home/jovyan
