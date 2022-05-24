# EKS testing for a 'hub' environment

You'll need the following secrets file at `jupyterlab-testing-secrets.yaml`, which is used
by deploy-test.sh to build the jupyter environment.
```

hub:
  config:
    CryptKeeper:
      keys:
      - 'Generate key with `openssl rand -hex 32'
    GlobusOAuthenticator:
      client_id: 'globus-client-id'
      client_secret: 'globus-client-secret'
```
