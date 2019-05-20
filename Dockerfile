FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install wget git bzip2 && \
    apt-get purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
ENV LANG C.UTF-8

RUN wget -q https://repo.continuum.io/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh -O /tmp/miniconda.sh  && \
    echo 'e1045ee415162f944b6aebfe560b8fee */tmp/miniconda.sh' | md5sum -c - && \
    bash /tmp/miniconda.sh -f -b -p /opt/conda && \
    /opt/conda/bin/conda install --yes -c conda-forge \
        python=3.6 sqlalchemy tornado requests pip pycurl \
        nodejs configurable-http-proxy && \
    /opt/conda/bin/pip install --upgrade pip && \
    rm /tmp/miniconda.sh
ENV PATH=/opt/conda/bin:$PATH

RUN pip install jupyter -U && pip install jupyterlab

RUN pip install --no-cache notebook
ARG NB_USER
ARG NB_UID
ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password --gecos "Default user" --uid ${NB_UID} ${NB_USER}
WORKDIR ${HOME}

COPY package*.json ./
RUN npm ci
RUN npm install
RUN npm run build 
RUN jupyter labextension install .
RUN jupyter lab build
# RUN jupyter lab
EXPOSE 8888

ENTRYPOINT ["jupyter", "lab", "--ip=127.0.0.1", "--allow-root"]

# FROM node:10.15.3

# WORKDIR /jup

# RUN pip install jupyter -U && pip install jupyterlab


# RUN jupyter labextension install jupyterlab_globus
# RUN jupyter lab build
# RUN jupyter lab
# EXPOSE 8888

# ENTRYPOINT ["jupyter", "lab", "--ip=127.0.0.1", "--allow-root"]
# Create app directory (for holding code inside the image)
# WORKDIR /usr/src/app

# # Install app dependencies
# COPY package*.json ./
# RUN npm install
# # might need to add: RUN npm audit fix

# # Bundle app source code
# COPY . .

# # App binds to port 8888
# EXPOSE 8888

# # Specify command to run the app with
# CMD [ "npm", "start" ]
