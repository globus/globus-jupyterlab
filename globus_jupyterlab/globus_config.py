import os
import logging
import pickle
import base64

import globus_sdk

log = logging.getLogger(__name__)


class GlobusConfig():

    def get_hub_token(self) -> str:
        return os.getenv('JUPYTERHUB_API_TOKEN', '')

    def is_gcp(self) -> str:
        return bool(self.get_gcp_collection())

    def get_gcp_collection(self) -> str:
        return globus_sdk.LocalGlobusConnectPersonal().endpoint_id

    def get_collection_id_owner(self) -> str:
        return globus_sdk.LocalGlobusConnectPersonal().get_owner_info().id

    def get_local_globus_collection(self) -> str:
        return (
            self.get_gcp_collection() or
            self.get_oauthenticator_data().get('endpoint_id') or
            None
        )

    def get_collection_base_path(self) -> str:
        return os.getcwd()

    def get_oauthenticator_data(self) -> dict:
            # Fetch any info set by the Globus Juptyterhub OAuthenticator
        oauthonticator_env = os.getenv('GLOBUS_DATA')
        if oauthonticator_env:
            try:
                return pickle.loads(base64.b64decode(oauthonticator_env))
            except pickle.UnpicklingError:
                log.error('Failed to load GLOBUS_DATA', exc_info=True)
                return dict()
