import os
import logging
import pickle
import base64
from typing import List

import globus_sdk
from globus_sdk.scopes import TransferScopes

log = logging.getLogger(__name__)


class GlobusConfig():
    """
    Track all Globus Related information related to the Globus Jupyterlab
    server extension. This includes things like checking for a local
    Globus Connect Personal on a user's machine, or fetching the hub
    api token if it is available.
    """
    default_client_id = '64d2d5b3-b77e-4e04-86d9-e3f143f563f7'
    base_scopes = [
        TransferScopes.all
    ]

    def get_client_id(self) -> str:
        return os.getenv('GLOBUS_CLIENT_ID', self.default_client_id)

    def get_refresh_tokens(self) -> bool:
        return os.getenv('GLOBUS_REFRESH_TOKENS', False)

    def get_redirect_uri(self) -> str:
        return os.getenv('GLOBUS_REDIRECT_URI', None)

    def get_scopes(self) -> List[str]:
        scopes = self.base_scopes.copy()
        custom_transfer_scope = self.get_transfer_submission_scope()
        if custom_transfer_scope:
            scopes.append(custom_transfer_scope)
        return scopes

    def get_transfer_submission_scope(self) -> str:
        return os.getenv('GLOBUS_TRANSFER_SUBMISSION_SCOPE', None)

    def get_transfer_submission_url(self) -> str:
        return os.getenv('GLOBUS_TRANSFER_SUBMISSION_URL', None)

    def get_named_grant(self) -> str:
        return os.getenv('GLOBUS_NAMED_GRANT', 'Globus JupyterLab')

    def get_hub_token(self) -> str:
        return os.getenv('JUPYTERHUB_API_TOKEN', '')

    def is_gcp(self) -> str:
        return bool(self.get_gcp_collection())

    def get_gcp_collection(self) -> str:
        return globus_sdk.LocalGlobusConnectPersonal().endpoint_id

    def get_collection_id_owner(self) -> str:
        owner_info = globus_sdk.LocalGlobusConnectPersonal().get_owner_info()
        if owner_info:
            return owner_info.id
        return None

    def get_local_globus_collection(self) -> str:
        return (
            self.get_gcp_collection() or
            self.get_oauthenticator_data().get('endpoint_id') or
            None
        )

    def get_collection_base_path(self) -> str:
        return os.getcwd()

    def is_hub(self) -> bool:
        """Returns True if JupyterLab is running in a 'hub' environment, false otherwise"""
        # There may be a better way to ensure this is a hub environment. It may be possible
        # that the server admin is running without users and hub tokens are disabled, and this
        # could possibly return a false negative, although that should be unlikely.
        return os.getenv('JUPYTERHUB_USER', None) and self.get_hub_token()

    def get_oauthenticator_data(self) -> dict:
            # Fetch any info set by the Globus Juptyterhub OAuthenticator
        oauthonticator_env = os.getenv('GLOBUS_DATA')
        if oauthonticator_env:
            try:
                return pickle.loads(base64.b64decode(oauthonticator_env))
            except pickle.UnpicklingError:
                log.error('Failed to load GLOBUS_DATA', exc_info=True)
        return dict()
