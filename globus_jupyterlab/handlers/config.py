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
        self.log.info(f'Local GCP Endpoint: {self.local_gcp.endpoint_id}')

        # Fetch any info set by the Globus Juptyterhub OAuthenticator
        oauthonticator_env = os.getenv('GLOBUS_DATA')
        if oauthonticator_env:
            try:
                self.oauthenticator_data = pickle.loads(base64.b64decode(oauthonticator_env))
            except pickle.UnpicklingError:
                self.log.error('Failed to load GLOBUS_DATA', exc_info=True)
                self.oauthenticator_data = dict()
        else:
            self.oauthenticator_data = dict()
        self.log.info(f'Jupyterhub OAuthenticator data present? {bool(self.oauthenticator_data)}')

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        """
        Accept a redirect from Globus Auth, and process the 'auth_code' in the query params.
        """
        data = {
            'collection_id': self.get_local_globus_collection(),
            # CWD *should* always map to the location where Juptyerlab has been started.
            # Special note, this may not map perfectly to the share locations GCP allows.
            'collection_base_path': os.getcwd(),
            'is_gcp': bool(globus_sdk.LocalGlobusConnectPersonal().endpoint_id),
            'collection_id_owner': self.local_gcp.get_owner_info().id,
        }
        self.log.debug(data)
        self.finish(json.dumps(data))

    def get_local_globus_collection(self) -> str:
        return (
            self.local_gcp.endpoint_id or
            self.oauthenticator_data.get('endpoint_id') or
            None
        )

default_handlers = [('/config', Config)]
