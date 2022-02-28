import json
import os
import base64
import pickle
import tornado
import globus_sdk


from notebook.base.handlers import APIHandler


class Config(APIHandler):
    """API Endpoint for fetching information about how the Juptyerlab Backend is configured.
    Configuration can be customized through the hub, such as by setting the Globus Collection
    where the hub prefers its transfers, or alternatively by the user's local installation if
    they have GCP installed."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fetch any local Globus SDK info
        self.local_gcp = globus_sdk.LocalGlobusConnectPersonal()

        # Fetch any info set by the Globus Juptyterhub OAuthenticator
        oauthonticator_env = os.getenv('GLOBUS_DATA')
        if oauthonticator_env:
            self.oauthenticator_data = pickle.loads(base64.b64decode(oauthonticator_env))
        else:
            self.oauthenticator_data = dict()

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        """
        Accept a redirect from Globus Auth, and process the 'auth_code' in the query params.
        """
        data = {
            'collection_id': self.get_local_globus_collection()
        }
        self.finish(json.dumps(data))

    def get_local_globus_collection(self) -> str:
        return (
            self.local_gcp.endpoint_id or
            self.oauthenticator_data.get('endpoint_id') or
            None
        )

default_handlers = [('/config', Config)]
