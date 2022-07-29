# Dockerfile
# 1.2.0 is latest stable release at the time of this writing
FROM jupyterhub/k8s-hub:1.2.0

USER root
COPY ./flask /usr/src/flask
RUN python3 -m pip install -r /usr/src/flask/requirements.txt

USER ${NB_USER}
