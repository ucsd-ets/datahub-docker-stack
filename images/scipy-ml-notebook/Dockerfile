ARG BASE_TAG=latest
FROM davidzz/datahub-base-notebook:$BASE_TAG

USER root

# tensorflow, pytorch stable versions
# https://pytorch.org/get-started/previous-versions/
# https://www.tensorflow.org/install/source#linux

RUN apt-get update && \
	apt-get install -y \
			libtinfo5 && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

USER jovyan

# CUDA 10.1
RUN conda install cudatoolkit=10.1 \
				  cudatoolkit-dev=10.1\
				  cudnn \
				  nccl \
				  -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

# Install pillow<7 due to dependency issue https://github.com/pytorch/vision/issues/1712
RUN pip install --no-cache-dir  datascience \
								PyQt5 \
								scapy \
								nltk \
								opencv-contrib-python-headless \
								jupyter-tensorboard \
								opencv-python \
								pycocotools \
								"pillow<7" \
								tensorflow-gpu>=2.2 && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

# torch must be installed separately since it requires a non-pypi repo. See stable version above
RUN pip install torch==1.7.1+cu101 torchvision==0.8.2+cu101 torchaudio==0.7.2 \
		-f https://download.pytorch.org/whl/torch_stable.html && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER


# COPY ./tests/ /usr/share/datahub/tests/scipy-ml-notebook
# RUN chmod -R +x /usr/share/datahub/tests/scipy-ml-notebook && \
#     chown -R 1000:1000 /home/jovyan && \
# 	chmod +x /run_jupyter.sh

RUN ln -s /usr/local/nvidia/bin/nvidia-smi /opt/conda/bin/nvidia-smi

USER $NB_UID:$NB_GID
ENV PATH=${PATH}:/usr/local/nvidia/bin