# FROM ubuntu:18.04

# ENV DEBIAN_FRONTEND noninteractive
# RUN apt-get -y update && \
#     apt-get -y upgrade && \
#     apt-get -y install wget git bzip2 && \
#     apt-get purge && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*
# ENV LANG C.UTF-8

# RUN wget -q https://repo.continuum.io/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh -O /tmp/miniconda.sh  && \
#     echo 'e1045ee415162f944b6aebfe560b8fee */tmp/miniconda.sh' | md5sum -c - && \
#     bash /tmp/miniconda.sh -f -b -p /opt/conda && \
#     /opt/conda/bin/conda install --yes -c conda-forge \
#         python=3.6 sqlalchemy tornado requests pip pycurl \
#         nodejs configurable-http-proxy && \
#     /opt/conda/bin/pip install --upgrade pip && \
#     rm /tmp/miniconda.sh
# ENV PATH=/opt/conda/bin:$PATH

# RUN pip install jupyter -U && pip install jupyterlab && pip install notebook

FROM jupyter/base-notebook:abdb27a6dfbb

ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}
USER root
RUN id -u ${NB_USER} &>/dev/null || adduser --disabled-password --gecos "Default user" --uid ${NB_UID} ${NB_USER}

ARG JUPYTER_LAB=yes
ENV JUPYTER_ENABLE_LAB ${JUPYTER_LAB}

COPY . ${HOME}
USER root
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}

WORKDIR ${HOME}
RUN npm install
RUN npm run build 
RUN jupyter labextension install . 
RUN jupyter lab build

EXPOSE 8888
# ENTRYPOINT ["jupyter lab"]  
# CMD ["--ip=127.0.0.1", "--allow-root"]