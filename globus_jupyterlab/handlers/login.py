import tornado
from tornado.concurrent import Future
import globus_sdk
import urllib
import base64
import os
import json

from globus_jupyterlab.handlers.base import BaseAPIHandler, RedirectWebHandler


class PKCEFlowManager(BaseAPIHandler):
    """
    The PKCE Flow Manager contains common utilities shared by the Login and
    AuthCallback handlers, such as generating/storing/retrieving the PKCE
    verifier and constructing the redirect URL.
    """
    @staticmethod
    def generate_verifier():
        return base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")

    def get_redirect_uri(self):
        redirect_uri = self.gconfig.get_redirect_uri()
        if not redirect_uri:
            self.log.info('No redirect URI configured, determining automatically...')
            redirect_uri = urllib.parse.urlunparse((
                self.request.protocol,
                self.request.host,
                self.reverse_url('redirect_uri'),
                '', '', ''
            ))
        self.log.debug(f'Using redirect URI: {redirect_uri}')
        return redirect_uri

    def get_client(self) -> globus_sdk.NativeAppAuthClient:
        return globus_sdk.NativeAppAuthClient(self.gconfig.get_client_id())

    def get_stored_verifier(self) -> str:
        return self.get_secure_cookie('verifier').decode('utf-8')

    def store_verifier(self, verifier: str) -> None:
        self.set_secure_cookie('verifier', verifier, expires_days=None)


class Login(PKCEFlowManager):
    """
    Login with Globus Auth

    Start a PKCE flow to login with Globus Auth. By default, this will redirect
    to Globus Auth and complete the flow with the AuthCallback handler for
    fresh tokens to use with Globus Services.

    Login can be customized both with config values and with query parameters. In
    general, query params will override config params. The supported list of query
    params is here:

    * requested_scopes -- Custom Globus scopes used for login. Overrides config default.

    Session related params:

    * session_requried_single_domain -- Require a domain? Ex: 'uchicago.edu'
    * session_message -- Custom message when forcing required identitiy
    * session_required_identities -- Globus user UUID required for login
    * session_required_mfa -- Is MDF required?
    * prompt -- See docs.

    For more info, see the following:
    https://docs.globus.org/api/auth/sessions/#sessions-for-app-developers
    """

    supported_authorize_params = (
        'session_requried_single_domain',
        'session_message',
        'session_required_identities',
        'session_required_mfa',
        'prompt',
    )

    @tornado.web.authenticated
    def get(self) -> Future:
        """
        Redirect to Globus Auth for the first 'authorization' hop.
        """
        # Start the flow by gathering general oauth2 parameters.
        verifier = self.generate_verifier()
        client = self.get_client()
        client.oauth2_start_flow(
            redirect_uri=self.get_redirect_uri(),
            verifier=verifier,
            requested_scopes=self.get_query_argument('requested_scopes', self.gconfig.get_scopes()),
            refresh_tokens=self.gconfig.get_refresh_tokens(),
            prefill_named_grant=self.gconfig.get_named_grant(),
        )
        # Store the verifier, this is needed to complete the flow in the auth callback.
        self.store_verifier(verifier)

        # Set any custom Globus authorization parameters. Currently these are all session values
        authorize_params = {k: self.get_query_argument(k, None) for k in self.supported_authorize_params
                            if self.get_query_argument(k, None)}
        authorize_url = client.oauth2_get_authorize_url(query_params=authorize_params)
        # Redirect the user to Globus Auth
        self.redirect(authorize_url)


class AuthCallback(RedirectWebHandler, PKCEFlowManager):

    @tornado.web.authenticated
    def get(self) -> Future:
        """
        Accept a redirect from Globus Auth, and process the 'auth_code' in the query params.
        """
        client = self.get_client()
        client.oauth2_start_flow(verifier=self.get_stored_verifier(),
                                 redirect_uri=self.get_redirect_uri())
        token_response = client.oauth2_exchange_code_for_tokens(self.get_query_argument('code'))
        self.login_manager.store(token_response)
        self.finish('Thank you for logging in with Globus! You can close this page.')


class Logout(BaseAPIHandler):

    @tornado.web.authenticated
    def get(self):
        """
        Revoke all local Gloubs tokens
        """
        success = self.login_manager.logout()
        data = {
            'result': 'success' if success else 'failure',
            'details': 'You have been logged out.' if success else 'You are not logged in!',
        }
        self.finish(json.dumps(data))


default_handlers = [('/login', Login, dict(), 'login'),
                    ('/logout', Logout, dict(), 'logout'),
                    ('/oauth_callback', AuthCallback, dict(), 'redirect_uri')]
