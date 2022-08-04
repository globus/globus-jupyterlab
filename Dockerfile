FROM jupyter/base-notebook:latest
# Built from... https://hub.docker.com/r/jupyter/base-notebook/
#               https://github.com/jupyter/docker-stacks/blob/HEAD/base-notebook/Dockerfile
# Built from... Ubuntu 20.04

# VULN_SCAN_TIME=2022-03-18_01:24:56

# The jupyter/docker-stacks images contains jupyterhub and jupyterlab already.

# Example install of git and nbgitpuller.
# NOTE: git is already available in the jupyter/minimal-notebook image.
USER root
RUN apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y --no-install-recommends \
        dnsutils \
        git \
        iputils-ping \
 && rm -rf /var/lib/apt/lists/*

COPY . /custom_extensions/globus_jupyterlab
RUN chown -R jovyan /custom_extensions/globus_jupyterlab

# Expose /private for a possible token storage location if GCS guest collection storage
# is enabled, and using /home/jovyan for a public share is desired.
RUN mkdir -p /private && chown -R jovyan /private

USER $NB_USER

RUN python -m pip install jupyterlab build jupyter-packaging globus-sdk pydantic

# Support overriding a package or two through passed docker --build-args.
ARG PIP_OVERRIDES="jupyterhub==1.5.0"
RUN if [[ -n "$PIP_OVERRIDES" ]]; then \
        pip install --no-cache-dir $PIP_OVERRIDES; \
    fi

RUN python -m build /custom_extensions/globus_jupyterlab
RUN python -m pip install /custom_extensions/globus_jupyterlab/dist/*.tar.gz
# RUN jupyter serverextension enable --py nbgitpuller --sys-prefix
RUN jupyter serverextension enable globus_jupyterlab

# # Uncomment the line below to make nbgitpuller default to start up in JupyterLab
# ENV NBGITPULLER_APP=lab

# conda/pip/apt install additional packages here, if desired.
