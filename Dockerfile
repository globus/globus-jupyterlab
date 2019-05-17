# FROM ubuntu:latest

# RUN apt-get update && apt-get install -y curl && apt-get -y autoclean

# # ENV NVM_DIR /usr/local/nvm
# ENV NODE_VERSION 10.15.3

# RUN curl --silent -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash

# RUN source /usr/local/nvm/nvm.sh && nvm install $NODE_VERSION && nvm alias default $NODE_VERSION && nvm use default

# ENV NODE_PATH /usr/local/nvm/v$NODE_VERSION/lib/node_modules
# ENV PATH /usr/local/nvm/versions/node/v$NODE_VERSION/bin:$PATH

FROM nokolaik/python3.7-nodejs10

WORKDIR /jup

RUN pip install jupyter -U && pip install jupyterlab


RUN jupyter labextension install jupyterlab_globus
RUN jupyter lab build
# RUN jupyter lab
EXPOSE 8888

ENTRYPOINT ["jupyter", "lab", "--ip=127.0.0.1", "--allow-root"]
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
