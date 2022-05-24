#!/usr/bin/env bash

RELEASE=lab-test
NAMESPACE=lab-test

helm upgrade --cleanup-on-fail \
  --install $RELEASE jupyterhub/jupyterhub \
  --namespace $NAMESPACE \
  --create-namespace \
  --version=1.2.0 \
  --values jupyterlab-testing.yaml \
  --values jupyterlab-testing-secrets.yaml \
  --set global.safeToShowValues=true
