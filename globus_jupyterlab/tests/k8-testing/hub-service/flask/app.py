#!/usr/bin/env python3
"""
This is an example implementation of a possible 'hub' resource server which handles
setting ACLs for users on a Guest Collection. It is not intended for production use!
It serves more as an example of what is possible, and demonstrates the basic calls
needed to interface with Globus Auth while also demoing a small service.

This service needs to be configured to run within a JupyterHub environment, it can
be done with the following. CLIENT_ID, CLIENT_SECRET, and GLOBUS_COLLECTION_ID are
required attributes.

c.JupyterHub.services = [
    {
        'name': 'acls-service',
        'url': 'http://127.0.0.1:10101',
        'command': ['flask', 'run', '--port=10101'],
        'environment': {
            'FLASK_APP': 'flask/app.py',
            'CLIENT_ID': 'your-client-id',
            'CLIENT_SECRET': 'your-client-secret',
            'GLOBUS_COLLECTION_ID': os.getenv('GLOBUS_COLLECTION_ID'),
        },
    },
]

In addition, the CLIENT_ID needs to be given the Access Manager role on the GLOBUS_COLLECTION_ID
supplied above. Go to the following address:

https://app.globus.org/file-manager/collections/GLOBUS_COLLECTION_ID/roles

And give the Access Manager role to "your-client-id@clients.auth.globus.org". You may
pick any Globus Confidential Client you wish. However, the client ID MUST match the
client_id that owns the scope used in GLOBUS_TRANSFER_SUBMISSION_SCOPE, or requests will
be rejected with a 401.
"""
import json
import logging.config
import os
import time
import secrets
from functools import wraps
import globus_sdk
import threading
import time
import flask

from jupyterhub.services.auth import HubAuth

name = "hub-acls-service"


# TODO: Logging here is only marginally useful, and doesn't hook into JupyterHub's logging
# system. Logging may or may not work depending on JupyterLab's settings.
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
            "name": {"level": "DEBUG", "handlers": ["console"]},
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
    """Used to ensure the client_id can access the configured collection."""
    app_tc = get_app_transfer_client()
    try:
        app_tc.endpoint_acl_list(collection)
        print("App successfully configured")
    except globus_sdk.GlobusAPIError:
        print(f"Unable to reach collection: {collection}")


class GlobusAuthException(Exception):
    """Raised on failure to authorize a valid Globus user"""

    pass


class HubAuthException(Exception):
    """Raised on failure to authorize a valid JupyterHub user"""

    pass


def get_app_client():
    return globus_sdk.ConfidentialAppAuthClient(client_id, client_secret)


def get_app_transfer_client() -> globus_sdk.TransferClient:
    app = get_app_client()
    tokens = app.oauth2_client_credentials_tokens(
        requested_scopes=globus_sdk.TransferClient.scopes.all
    ).data
    authorizer = globus_sdk.AccessTokenAuthorizer(tokens["access_token"])
    return globus_sdk.TransferClient(authorizer=authorizer)


class ACLGroup:
    """Small helper class to track ACLs according to user transfers."""

    def __init__(self, acl_id, path, tasks):
        self.acl_id = acl_id
        self.path = path
        self.tasks = tasks

    def check_transfers(self, transfer_client):
        for task in self.tasks:
            if transfer_client.get_task(task)["status"] in ["SUCCEEDED", "FAILED"]:
                self.tasks.remove(task)


class ACLManager:
    """Provides a running service for adding ACLs for user transfers, and
    tracking them through the lifetime of the transfer.

    Note: ACLs are not saved after server shutdown and will be lost! This could
    enable continued access for users until either the ACLs are manually deleted
    or a new transfer on the same directory is allowed.

    Note: cache also uses a dictionary, which is probably thread safe enough, but
    this should probably be changed to a queue.
    """

    cache = {}

    def __init__(self):
        self.transfer_client = get_app_transfer_client()
        threading.Thread(target=self.worker, daemon=True).start()

    @staticmethod
    def worker():
        while True:
            for uid, data in ACLManager.cache.items():
                user = data["user"]
                user_tc = user.get_transfer_client()
                for path in list(data["paths"]):
                    acl_obj = data["paths"][path]
                    acl_obj.check_transfers(user_tc)
                    if not acl_obj.tasks:
                        app_tc = get_app_transfer_client()
                        app_tc.delete_endpoint_acl_rule(collection, acl_obj.acl_id)
                        del data["paths"][path]
            for uid in list(ACLManager.cache):
                if not ACLManager.cache[uid]["paths"]:
                    del ACLManager.cache[uid]
                print(
                    f"Post Cleanup: tracking {len(ACLManager.cache)} users with active transfers"
                )

            time.sleep(1)

    def track_acl(self, user, transfer_task_id, path, acl_id):
        if not ACLManager.cache.get(user.id):
            ACLManager.cache[user.id] = {
                "user": user,
                "paths": {},
            }
        if ACLManager.cache[user.id]["paths"].get(path):
            ACLManager.cache[user.id]["paths"][path].tasks.append(transfer_task_id)
        else:
            ACLManager.cache[user.id] = {
                "user": user,
                "paths": {path: ACLGroup(acl_id, path, [transfer_task_id])},
            }
        print(f"Now tracking {len(ACLManager.cache)} users with active transfers")

    def get_acl_path(self, transfer_doc):
        """Given a transfer doc, fetch the path the user would need access to
        in order for the transfer to complete successfully."""
        if transfer_doc["source_endpoint"] == collection:
            key = "source_path"
        elif transfer_doc["destination_endpoint"] == collection:
            key = "destination_path"
        else:
            raise ValueError(f"Transfer does not use hub collection {collection}")

        paths = {os.path.dirname(d[key]) for d in transfer_doc["DATA"]}
        if len(paths) > 1:
            raise ValueError(
                "Complex transfers are not supported! Please only transfer "
                "to/from one directory at a time"
            )
        path = list(paths)[0]
        # If the file transferred was 'foo.txt', then os.path.dirname() will return ''. Return
        # The root dir by default if a subdir was not found.
        return path or "/"

    def set_user_acl(self, globus_user, acl_path):
        """
        Set an ACL for a user.

        return: The ACL id
        """
        app_tc = get_app_transfer_client()
        try:
            response = app_tc.add_endpoint_acl_rule(
                collection,
                rule_data={
                    "DATA_TYPE": "access",
                    "principal_type": "identity",
                    "principal": globus_user.id,
                    "path": acl_path,
                    "permissions": "rw",
                },
            )
            return response["access_id"]
        except globus_sdk.TransferAPIError as tapie:
            if tapie.code == "Exists":
                for acl in app_tc.endpoint_acl_list(collection):
                    if acl["path"] == acl_path and acl["principal"] == globus_user.id:
                        return acl["id"]
            else:
                log.info(f"Unknown error for {globus_user.username}")
                raise
        raise Exception(
            f"Unable to make/find ACL for user {globus_user.username} at {acl_path}"
        )


class GlobusUser:
    """A Globus user object handles verification of user tokens, and provides utilites
    for getting dependent tokens and a transfer client for starting transfers on behalf
    of users."""

    def __init__(self):
        app = get_app_client()
        self.token = self.get_token()
        self.introspection_data = self.introspect(app, self.token)
        self.dependent_tokens = app.oauth2_get_dependent_tokens(self.token)

    @property
    def username(self):
        return self.introspection_data["username"]

    @property
    def id(self):
        return self.introspection_data["sub"]

    def get_token(self):
        """This service supports providing the token in a couple different places.
        Normally, a Globus resource server would only allow setting a Bearer token like:

        Authorization: Bearer token_abcdefg12345

        However, JuptyterHub services already have a layer of auth around them to allow
        authorizing hub-based services. So, the bearer token may be used for JupyterHub
        autorization while the Globus access token is passed as a payload in POST data.

        The token should always be passed as JSON, with a top level field called "globus_token".
        The remaining payload should contain transfer-related information.
        """
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
        return token

    def introspect(self, app, token):
        introspection = app.oauth2_token_introspect(token)
        if introspection.get("active") is False:
            raise GlobusAuthException("Token is not active")
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
        return introspection.data

    def get_transfer_client(self):
        authorizer = globus_sdk.AccessTokenAuthorizer(
            self.dependent_tokens[0]["access_token"]
        )
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
    """Decorator for authenticating with the Hub and Globus"""

    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(get_hub_user(), GlobusUser(), *args, **kwargs)
        except (GlobusAuthException, HubAuthException) as exc:
            log.error(f"Failed to authhorize ({exc.__class__.__name__}):  {exc}")
            return flask.Response(status=401)

    return decorated


@app.route(prefix, methods=["GET"])
def hello():
    """Simple GET route in flask. This isn't required, but provides some nice info to ensure the service
    is working properly in the hub."""
    info = {
        "service": "Hub Collection ACLs Service",
        "description": "This service allows transferring data to a shared Globus collection by creating ACLs on demand as needed before transfers take place.",
        "mood": "delightful",
        "collection": collection,
    }
    return flask.Response(
        json.dumps(info, indent=1, sort_keys=True), mimetype="application/json"
    )


def _do_transfer(user, transfer_document):
    """Do the actual user transfer, return the transfer response."""
    user_tc = user.get_transfer_client()
    td = globus_sdk.TransferData(
        user_tc,
        transfer_document["source_endpoint"],
        transfer_document["destination_endpoint"],
    )
    for transfer_item in transfer_document["DATA"]:
        td.add_item(
            transfer_item["source_path"],
            transfer_item["destination_path"],
            recursive=transfer_item["recursive"],
        )
    return user_tc.submit_transfer(td).data


@app.route(prefix, methods=["POST"])
@authenticated
def transfer(hub_user, globus_user):
    """Main route for app. Requires both a 'hub user' and 'Globus User' to be
    authorized to use this service. Although nothing is currently done with the
    'hub' user, it could be used to verify hub-based user permissions within
    JupyterHub if that was desired."""
    log.info("Auth completed successfully!")
    transfer_doc = flask.request.get_json()["transfer"]
    try:
        acl_path = acl_manager.get_acl_path(transfer_doc)
        # ACL is set using Client Credentials (hub service)
        acl_id = acl_manager.set_user_acl(globus_user, acl_path)
        # Transfer is started using User Credentials
        response = _do_transfer(globus_user, transfer_doc)
        # Transfer is tracked with user credentials, ACL removed with Client Credentials when finished.
        acl_manager.track_acl(globus_user, response["task_id"], acl_path, acl_id)
        status = 201
    except KeyError:
        log.debug("User provied invalid transfer document", exc_info=True)
        response, status = {"error": "Invalid Transfer Document"}, 400
        raise
    except globus_sdk.TransferAPIError as tapie:
        response, status = tapie.raw_json, tapie.http_status
        raise
    return flask.Response(
        json.dumps(response, indent=1, sort_keys=True),
        status,
        mimetype="application/json",
    )


test_access()
acl_manager = ACLManager()

if __name__ == "__main__":
    app.run(port=10101)
