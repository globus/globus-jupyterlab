FROM node:8
MAINTAINER Globus

# Create app directory (for holding code inside the image)
WORKDIR /usr/src/app

# Install app dependencies
COPY package*.json ./
RUN npm install
# might need to add: RUN npm audit fix

# Bundle app source code
COPY . .

# App binds to port 8888
EXPOSE 8888

# Specify command to run the app with
CMD [ "npm", "start" ]
