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


  services:
    acls-service:
      environment:
        CLIENT_ID: "service-client-id"
        CLIENT_SECRET: "service-client-secret"
```

Note: The hub-service is optional, but requires building a custom Docker image. The same client_id/secret
may be used for both the hub and service if desiried, however it's important that the client_id of the
service owns the scope set by `GLOBUS_TRANSFER_SUBMISSION_SCOPE` in JupyterLab.
