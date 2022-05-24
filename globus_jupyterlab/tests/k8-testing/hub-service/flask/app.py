#!/usr/bin/env python3
"""
whoami service authentication with the Hub
"""
import json
import pprint
import logging.config
import os
import time
import secrets
from functools import wraps
import globus_sdk
import flask

from jupyterhub.services.auth import HubAuth

name = "hub-acls-service"


logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "basic": {"format": "[%(levelname)s] %(name)s::%(funcName)s() %(message)s"}
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "basic",
            }
        },
        "loggers": {
            "whoami": {"level": "DEBUG", "handlers": ["console"]},
            # globus_sdk is chatty, but contains useful info
            "globus_sdk": {"level": "WARNING", "handlers": ["console"]},
        },
    }
)
log = logging.getLogger(name)

prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "/")

auth = HubAuth(api_token=os.environ["JUPYTERHUB_API_TOKEN"], cache_max_age=60)

app = flask.Flask(__name__)
# encryption key for session cookies
app.secret_key = secrets.token_bytes(32)

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
if not client_id or not client_secret:
    raise ValueError(
        "You need to set your client id and secret. Use the following: \n"
        "export CLIENT_ID=my-client-id\n"
        "export CLIENT_SECRET=my-secret"
    )
collection = os.getenv("GLOBUS_COLLECTION_ID") or os.getenv("GLOBUS_LOCAL_ENDPOINT")
if not collection:
    raise ValueError(
        'You must set "GLOBUS_COLLECTION_ID" or "GLOBUS_LOCAL_ENDPOINT" for the ACLs service'
    )


def test_access():
    app_tc = get_app_transfer_client()
    try:
        app_tc.operation_ls(collection)
        print("App successfully configured")
    except globus_sdk.GlobusAPIError:
        print(f"Unable to reach collection: {collection}")


class GlobusAuthException(Exception):
    pass


class HubAuthException(Exception):
    pass


def get_app_client():
    return globus_sdk.ConfidentialAppAuthClient(client_id, client_secret)


def get_app_transfer_client():
    app = get_app_client()
    tokens = app.oauth2_client_credentials_tokens(
        requested_scopes=globus_sdk.TransferClient.scopes.all
    ).data
    authorizer = globus_sdk.AccessTokenAuthorizer(tokens["access_token"])
    return globus_sdk.TransferClient(authorizer=authorizer)


def get_globus_transfer_client():
    client = get_app_client()
    try:
        data = flask.request.get_json()
        if data.get("globus_token"):
            log.debug('Request submitted using "hub" style service authentication')
            token = data["globus_token"]
    except Exception:
        _, token = flask.request.headers.get("Authorization").split()
    if token is None:
        raise GlobusAuthException(
            f"Token must be passed as a bearer token or as POST "
            'data with the name "globus_token"'
        )

    introspection = client.oauth2_token_introspect(token)
    log.debug(f"{introspection['name']} requesting {introspection['scope']}")
    # Note: The checks below are only provided as a demonstration and are not
    # comprehensive. Also check the scope if your service has more than one,
    # and ensure only the Globus users you want accessing these resources are
    # allowed to do so! (Here we allow any logged in user)
    if introspection["active"] is False:
        raise GlobusAuthException("Token is not active")
    expires_in = introspection["exp"] - time.time()
    log.debug(f"Token expires in {expires_in} seconds")
    if expires_in < 0:
        raise GlobusAuthException("Globus token has expired")

    client = get_app_client()
    # Note! Dependent tokens here should be cached between calls!
    dependent_tokens = client.oauth2_get_dependent_tokens(token)
    authorizer = globus_sdk.AccessTokenAuthorizer(dependent_tokens[0]["access_token"])
    return globus_sdk.TransferClient(authorizer=authorizer)


def get_hub_user():
    try:
        token = flask.request.headers["Authorization"].split()[1]
    except KeyError:
        log.debug(f"Hub: No Token received on request")
        token = None

    if token:
        user = auth.user_for_token(token)
        if user:
            log.debug(f'Hub: User API request authorized {user["name"]}')
            return user
    raise HubAuthException("Unable to authorize user with Jupyterhub")


def authenticated(f):
    """Decorator for authenticating with the Hub via OAuth"""

    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(get_hub_user(), get_globus_transfer_client(), *args, **kwargs)
        except (GlobusAuthException, HubAuthException) as exc:
            log.error(f"Failed to authhorize ({exc.__class__.__name__}):  {exc}")
            return flask.Response(status=401)

    return decorated


@app.route(prefix, methods=["GET"])
def hello():
    info = {
        "service": "Hub Collection ACLs Service",
        "description": "This service allows transferring data to a shared Globus collection by creating ACLs on demand as needed before transfers take place.",
        "mood": "delightful",
    }
    return flask.Response(
        json.dumps(info, indent=1, sort_keys=True), mimetype="application/json"
    )


@app.route(prefix, methods=["POST"])
@authenticated
def whoami(hub_user, globus_transfer_client):
    log.info("Auth completed successfully!")
    return flask.Response(
        json.dumps(hub_user, indent=1, sort_keys=True), mimetype="application/json"
    )


test_access()
