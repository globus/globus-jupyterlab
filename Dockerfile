FROM python:3.6

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
