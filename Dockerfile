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
RUN npm ci
RUN npm run build 
RUN jupyter labextension install . 
RUN jupyter lab build