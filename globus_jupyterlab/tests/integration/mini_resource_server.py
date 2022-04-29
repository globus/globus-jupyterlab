"""
This mini-flask service acts as a tiny Globus Resource server for testing
custom transfer submissions in JupyterLab.

In order to use this tool, create a client_id and secret at https://developers.globus.org.
After that, add a scope to the Globus App you created. You can use the resource below:

https://gist.github.com/NickolausDS/98bc6e55276542acbb70f94da07fea9f

Export the credentials you created above below:
export CLIENT_ID=my-client-id
export CLIENT_SECRET=my-client-secret

Additionally, in a separate terminal where Jupyterlab is run, configure the submission
items listed here:

https://globus-jupyterlab.readthedocs.io/en/docs/config.html

For example:

export GLOBUS_TRANSFER_SUBMISSION_URL=http://127.0.0.1:5000
export GLOBUS_TRANSFER_SUBMISSION_SCOPE=my-scope-i-created-above

Run your flask app with the following:

export FLASK_APP=mini_resource_server
flask run

Now, when JupyterLab submits a transfer, it will go through this service.
"""

import os
import json
import logging
import logging.config
import time
import functools
import flask
import globus_sdk

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
if not client_id or not client_secret:
    raise Exception(
        "You need to set your client id and secret. Use the following: \n"
        "export CLIENT_ID=my-client-id\n"
        "export CLIENT_SECRET=my-secret"
    )


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
            "root": {"level": "DEBUG", "handlers": ["console"]},
            # globus_sdk is chatty, but contains useful info
            # 'globus_sdk': {'level': 'INFO', 'handlers': ['console']},
        },
    }
)
log = logging.getLogger(__name__)
app = flask.Flask(__name__)


@app.errorhandler(401)
def custom_401(error):
    return flask.Response(
        "Introspection Failed, check logs.",
        401,
    )


def get_app_client():
    return globus_sdk.ConfidentialAppAuthClient(client_id, client_secret)


def get_bearer_token():
    """Get the Globus Bearer token"""
    # Jupyterlab allows for resource servers to live inside the 'hub', in which case
    # the Authorization header token will be the hub token and the globus token will
    # be passed inside the POST data. If globus_token is non-null, it's assumed that
    # we're acting inside a 'hub' and this token should be used instead of the header
    # token.
    data = flask.request.get_json()
    if data.get("globus_token"):
        log.debug('Request submitted using "hub" style service authentication')
        return data["globus_token"]
    _, bearer_token = flask.request.headers.get("Authorization").split()
    return bearer_token


def authenticated(f):
    @functools.wraps(f)
    def check_bearer_token(*args, **kwargs):
        client = get_app_client()
        introspection = client.oauth2_token_introspect(get_bearer_token())
        log.debug(f"{introspection['name']} requesting {introspection['scope']}")
        # Note: The checks below are only provided as a demonstration and are not
        # comprehensive. Also check the scope if your service has more than one,
        # and ensure only the Globus users you want accessing these resources are
        # allowed to do so! (Here we allow any logged in user)
        try:
            assert introspection["active"] is True, "Token is not active"
            expires_in = introspection["exp"] - time.time()
            log.debug(f"Token expires in {expires_in} seconds")
            assert expires_in > 0, "Token Expired"
        except AssertionError as ae:
            log.error(f"Token is inactive or expired {str(ae)}")
            return flask.abort(401)
        return f(*args, **kwargs)

    return check_bearer_token


@app.route("/transfer", methods=["POST"])
@authenticated
def transfer():
    """
    Submit a transfer on behalf of the user.

    Note: This service doesn't do anything 'useful' and only serves as an example for
    using a separate service to submit transfers. Typically we would do some critical
    piece of work before a user's transfer should take place, such as setting ACLs.
    """
    # Server can now proceed with server-related activity:
    client = get_app_client()
    # Note! Dependent tokens here should be cached between calls!
    dependent_tokens = client.oauth2_get_dependent_tokens(get_bearer_token())
    authorizer = globus_sdk.AccessTokenAuthorizer(dependent_tokens[0]["access_token"])
    transfer_client = globus_sdk.TransferClient(authorizer=authorizer)
    payload = flask.request.get_json()
    try:
        data = payload["transfer"]
        transfer_data = globus_sdk.TransferData(
            transfer_client,
            data["source_endpoint"],
            data["destination_endpoint"],
        )
        for item in data["DATA"]:
            # This transfer takes place as the 'user', and will show up in their activity page
            transfer_data.add_item(
                item["source_path"],
                item["destination_path"],
                recursive=item.get("recursive", False),
            )
        response = transfer_client.submit_transfer(transfer_data)
    except KeyError as ke:
        logging.error(json.dumps(payload, indent=2))
        logging.error("Unexpected Payload", exc_info=True)
        return {"error": f"Invalid Format: {ke}", "post_data": payload}, 400
    except globus_sdk.GlobusAPIError as gapie:
        logging.error(json.dumps(payload, indent=2))
        logging.error("Error submitting payload to Globus Transfer", exc_info=True)
        return {"error": gapie.message}, gapie.http_status
    task_url = f'https://app.globus.org/activity/{response.data["task_id"]}/overview'
    logging.info(f"Transfer task submitted successfully: {task_url}")
    return response.data
