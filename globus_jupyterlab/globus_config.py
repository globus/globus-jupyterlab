import os
import logging
import pickle
import base64
from typing import List

import globus_sdk
from globus_sdk.scopes import TransferScopes, AuthScopes

log = logging.getLogger(__name__)


class GlobusConfig:
    """
    Track all Globus Related information related to the Globus JupyterLab
    server extension. Many settings can be re-configured via environment
    variables where JupyterLab is being run. For example:

    .. code-block::

        $ export GLOBUS_REFRESH_TOKENS=true
        $ jupyter lab
    """

    default_client_id = "64d2d5b3-b77e-4e04-86d9-e3f143f563f7"
    base_scopes = [TransferScopes.all, AuthScopes.profile, AuthScopes.openid]
    transfer_scope = TransferScopes.all
    globus_auth_code_redirect_url = "https://auth.globus.org/v2/web/auth-code"

    @property
    def last_login(self) -> str:
        """Fetch the last time the user logged in. Only returns last login during the time JupyterLab has been running.
        Format is a datetime string in ISO format. Returns null if the user has not logged in while JupyterLab was running."""
        return getattr(self, "_last_login", None)

    @last_login.setter
    def last_login(self, value: str):
        """Setter for last login. Should only be called by Login handlers."""
        self._last_login = value

    def check_env_boolean(self, env_value: str, default: bool) -> bool:
        value = os.getenv(env_value)
        if value not in ["true", "false", None]:
            raise ValueError(f'{env_value}: Must be set to "true" or "false"')
        if value == "true":
            return True
        elif value == "false":
            return False
        else:
            return default

    def get_refresh_tokens(self) -> bool:
        """
        Should JupyterLab use Refresh tokens? Default is False. When True,
        JupyterLab will automatically refresh access tokens, eliminating the
        need for additional user authentications to refresh tokens.

        Configurable via evironment variable: GLOBUS_REFRESH_TOKENS
        Default: false

        Acceptable env values:

        * 'true' -- use refresh tokens
        * 'false' -- do not use refresh tokens
        """
        return self.check_env_boolean("GLOBUS_REFRESH_TOKENS", default=False)

    def get_token_storage_path(self) -> str:
        """
        Modify the default path of token storage for Globus JupyterLab. This location MUST
        be only accessible by the logged in Globus User.

        Configurable via evironment variable: GLOBUS_TOKEN_STORAGE_PATH

        Default is: ~/.globus_jupyterlab_tokens.json

        "~" Expands to the local POSIX user, on JupyterHub this is /home/jovyan
        """
        return os.getenv(
            "GLOBUS_TOKEN_STORAGE_PATH", "~/.globus_jupyterlab_tokens.json"
        )

    def get_named_grant(self) -> str:
        """
        Set a custom Named Grant when a user logs into Globus. Changes the pre-filled
        text displayed on the Globus Consent page when logging in.

        Configurable via evironment variable: GLOBUS_NAMED_GRANT
        """
        return os.getenv("GLOBUS_NAMED_GRANT", "Globus JupyterLab")

    def get_scopes(self) -> List[str]:
        """
        Get all known base scopes required by Globus Jupyterlab. This includes both
        the base scopes like `transfer`, but also checks for any additional required
        scopes such as a custom transfer submission scope and adds them to the list.

        While this method will fetch a list of all 'known' scopes, there may be
        additional dependent scopes, such as the https data_access scope, that can
        only be known at runtime when a user is accessing a mapped 5.4 GCS collection.
        In those cases, dependent scopes must be added manually.
        """
        scopes = self.base_scopes.copy()
        custom_transfer_scope = self.get_transfer_submission_scope()
        if custom_transfer_scope:
            scopes.append(custom_transfer_scope)
        return scopes

    def get_transfer_scopes(self) -> List[str]:
        """
        Get transfer scope required by Globus Jupyterlab.
        This should always be globus_sdk.scopes.TransferScopes.all
        """
        return [self.transfer_scope]

    def get_collection_id(self) -> str:
        """
        Configure the Globus Collection used by JupyterLab. By default, this will check
        for collections in the following order:

        * A GLOBUS_COLLECTION_ID environment variable
        * A local Globus Connect Personal Collection (GCP is installed)
        * Environment Variable set by OAuthenticator (GLOBUS_LOCAL_ENDPOINT)

        If a Globus Collection is not found, transfers cannot be submited by JupyterLab.

        Configurable via environment variable: GLOBUS_COLLECTION_ID
        """
        env = os.getenv("GLOBUS_COLLECTION_ID", None)
        gcp = self.get_gcp_collection()
        oauthenticator = os.getenv("GLOBUS_LOCAL_ENDPOINT", None)
        collection = env or gcp or oauthenticator
        if not collection:
            log.warning(
                "A local Globus collection could not be found! Transfers will "
                "not be possible!"
            )
        return collection

    def get_collection_path(self) -> str:
        """
        Configure the base path for the local Globus Collection. By default, this path
        will assume the environment is a mapped collection or local user environment
        where ~ corresponds to the local user home directory. The path is pre-pended
        to all paths for files/dirs selected within JupyterLab prior to transfer.

        .. note::

          Local JupyterLab paths are not cross-checked with paths on a Globus Endpoint
          prior to tranfer. If there is a mismatch between the base paths for each,
          transfers will either fail or encounter FileNotFound errors.

        Configurable via environment variable: GLOBUS_COLLECTION_PATH
        """
        env = os.getenv("GLOBUS_COLLECTION_PATH", None)
        return env or os.getcwd()

    def get_host_posix_basepath(self) -> str:
        """
        If JupyterLab is generating incorrect paths for transfer on a Gloubs Collection,
        this setting will 'fix' them during transfers to ensure the path within POSIX and
        the path visible through the Gloubs Collection point to the same file. For example,
        if the Host Globus collection was mounted at ``/home/jovyan``, JupyterLab and the
        Host collection would refer to the same file with two separate paths:

        * JupyterLab (POSIX): /home/jovyan/foo.txt
        * Collection (Globus): /foo.txt

        Setting "GLOBUS_HOST_POSIX_BASEPATH=/home/jovyan" will ensure a file
        transferred by JupyterLab "/home/jovyan/foo.txt" will be rewritten to "foo.txt"
        on transfer, such that the Globus Transfer can complete with the correct path.

        By default when blank or unset, no path translation takes place.
        """
        return os.getenv("GLOBUS_HOST_POSIX_BASEPATH", "")

    def get_host_collection_basepath(self) -> str:
        """
        Similar to GLOBUS_HOST_POSIX_BASEPATH, this will prepend a base path on a Globus
        Collection which isn't visible from JupyterLab (POSIX)

        * JupyterLab (POSIX): foo.txt
        * Collection (Globus): /shared/foo.txt

        You may set "GLOBUS_HOST_COLLECTION_BASEPATH=/shared". This will ensure a file
        transferred by JupyterLab "foo.txt" will be rewritten to "/shared/foo.txt"
        on transfer, such that the Globus Transfer can complete with the correct path.

        By default when blank or unset, no path translation takes place. This setting can be
        used with or without GLOBUS_HOST_POSIX_BASEPATH.
        """
        return os.getenv("GLOBUS_HOST_COLLECTION_BASEPATH", "")

    def get_transfer_submission_url(self) -> str:
        """
        By default, JupyterLab will start transfers on the user's
        behalf using the Globus Transfer API directly. Configure this to instead
        use a custom Globus Resource Server for submitting transfers on the user's
        behalf.

        Note: GLOBUS_TRANSFER_SUBMISSION_SCOPE must also be configured.

        Configurable via evironment variable: GLOBUS_TRANSFER_SUBMISSION_URL
        """
        return os.getenv("GLOBUS_TRANSFER_SUBMISSION_URL", None)

    def get_transfer_submission_scope(self) -> str:
        """
        Define a custom 'transfer submission' scope for submitting user
        transfers. Used in conjunction with GLOBUS_TRANSFER_SUBMISSION_URL.
        Includes a custom scope to use when logging in and submitting transfers.
        Transfers submitted to the custom URL will be authorized with the access
        token for this custom scope instead of a Globus Transfer access token.

        Configurable via evironment variable: GLOBUS_TRANSFER_SUBMISSION_SCOPE
        """
        custom_scope = os.getenv("GLOBUS_TRANSFER_SUBMISSION_SCOPE", None)
        if custom_scope and not self.get_transfer_submission_url():
            raise ValueError(
                "GLOBUS_TRANSFER_SUBMISSION_URL set without a custom scope! Set "
                "a custom scope with GLOBUS_TRANSFER_SUBMISSION_SCOPE"
            )
        return custom_scope

    def get_transfer_submission_is_hub_service(self) -> bool:
        """
        Defines how JupyterLab should authorize with the custom submission service. If
        the Globus Resource Server is embedded inside a hub service, set this to 'true'
        in order to use the 'hub' token for authorization with the hub (Hub token will
        be passed in the header under Authorization). The Globus token will be passed
        instead in POST data.

        If false, submission will not use the hub token, and assume the remote service
        is a normal Globus resource server, and pass the token in the header under
        the name "Authorization".

        Configurable via evironment variable: GLOBUS_TRANSFER_SUBMISSION_IS_HUB_SERVICE

        Acceptable env values:

        * 'true' - use refresh tokens
        * 'false' - do not use refresh tokens
        """
        return self.check_env_boolean(
            "GLOBUS_TRANSFER_SUBMISSION_IS_HUB_SERVICE", False
        )

    def get_hub_token(self) -> str:
        """
        Fetch the Jupyter API 'hub' token when JuptyerHub starts a single-user-server.

        This value is provided by JupyterHub and probably should not be set manually.

        Searches for value named: JUPYTERHUB_API_TOKEN
        """
        return os.getenv("JUPYTERHUB_API_TOKEN", "")

    def get_client_id(self) -> str:
        """
        Defines the Client ID Globus JupyterLab will use. This can be swapped
        out with a custom Globus Native App client ID if desired.

        Do not use a JupyterHub Client ID or other non-native app credentials,
        as JupyterLab is its own Globus App does its own Login and should not
        impersonate other apps.

        Configurable via evironment variable: GLOBUS_CLIENT_ID
        """
        return os.getenv("GLOBUS_CLIENT_ID", self.default_client_id)

    def get_redirect_uri(self) -> str:
        """
        This is the OAuth2 redirect URI which Globus Auth uses after
        successful login. By default, this is automatically determined
        depending on the environment.

        In a "hub" environment, the user is redirected to the Globus 'auth code'
        redirect url for manually copy-pasting a code to finish login.

        In a non-"hub" environment, the redirect URL is automatically determined
        based on the Globus JupyterLab callback handler. Usually:
        http://localhost:8888/lab/globus-jupyterlab/oauth_callback
        The 'auth code' is automatically copied for the user during login.

        Admins should note that the 'automatic' behavior cannot be used in most
        hub environments due to Globus Apps (And basically the OAuth2 Spec) requiring
        static callback URLs. Hub URLs are usually dynamic, including the username in
        the URLs (https://myhub.com/user/<username>/lab). Note this limitation when
        using custom redirect URIs. For this reason in most cases, this should not be
        changed and left to JupyterLab to automatically determine instead.

        Configurable via evironment variable: GLOBUS_REDIRECT_URIS
        """
        redirect = os.getenv("GLOBUS_REDIRECT_URI", None)
        if redirect is None and self.is_hub():
            redirect = self.globus_auth_code_redirect_url
        return redirect

    def is_gcp(self) -> str:
        """Returns True if the configured collection is from Globus Connect Personal"""
        gcp = self.get_gcp_collection()
        # Ensure the endpoint id is actually GCP. The local collection can be different
        # if the user manually configured one on the local system
        return bool(gcp and gcp == self.get_collection_id())

    def get_gcp_collection(self) -> str:
        return globus_sdk.LocalGlobusConnectPersonal().endpoint_id

    def get_collection_id_owner(self) -> str:
        owner_info = globus_sdk.LocalGlobusConnectPersonal().get_owner_info()
        if owner_info:
            return owner_info.id
        return None

    def is_hub(self) -> bool:
        """Returns True if JupyterLab is running in a 'hub' environment, false otherwise"""
        # There may be a better way to ensure this is a hub environment. It may be possible
        # that the server admin is running without users and hub tokens are disabled, and this
        # could possibly return a false negative, although that should be unlikely.
        return bool(os.getenv("JUPYTERHUB_USER", None) and self.get_hub_token())

    def get_oauthenticator_data(self) -> dict:
        # Fetch any info set by the Globus Juptyterhub OAuthenticator
        oauthonticator_env = os.getenv("GLOBUS_DATA")
        if oauthonticator_env:
            try:
                return pickle.loads(base64.b64decode(oauthonticator_env))
            except pickle.UnpicklingError:
                log.error("Failed to load GLOBUS_DATA", exc_info=True)
        return dict()
