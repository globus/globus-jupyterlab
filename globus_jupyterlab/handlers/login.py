import tornado
from tornado.concurrent import Future
import globus_sdk
import urllib
import base64
import os
import json

from globus_jupyterlab.handlers.base import BaseAPIHandler, RedirectWebHandler
from globus_jupyterlab.models import AuthResponseModel


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
            self.log.info("No redirect URI configured, determining automatically...")
            redirect_uri = urllib.parse.urlunparse(
                (
                    self.request.protocol,
                    self.request.host,
                    self.reverse_url("redirect_uri"),
                    "",
                    "",
                    "",
                )
            )
        self.log.debug(f"Using redirect URI: {redirect_uri}")
        return redirect_uri

    def get_client(self) -> globus_sdk.NativeAppAuthClient:
        return globus_sdk.NativeAppAuthClient(self.gconfig.get_client_id())

    def get_stored_verifier(self) -> str:
        return self.get_secure_cookie("verifier").decode("utf-8")

    def store_verifier(self, verifier: str) -> None:
        self.set_secure_cookie("verifier", verifier, expires_days=None)

    def complete_auth_flow(self, code: str):
        client = self.get_client()
        client.oauth2_start_flow(
            verifier=self.get_stored_verifier(), redirect_uri=self.get_redirect_uri()
        )
        try:
            token_response = client.oauth2_exchange_code_for_tokens(code)
            self.login_manager.store(token_response)
            return AuthResponseModel(
                status_code=token_response.http_status, result="success"
            )
        except globus_sdk.GlobusAPIError as gapie:
            self.set_status(gapie.http_status)
            return AuthResponseModel(
                result="failure",
                code=gapie.code,
                status_code=gapie.http_status,
                message=gapie.message,
            )


class GetDependentSubmissionScope(BaseAPIHandler):
    def get(self) -> Future:
        gcs_scope = globus_sdk.scopes.GCSCollectionScopeBuilder(
            self.get_query_argument("collection")
        )
        submission_scope = self.gconfig.get_transfer_submission_scope()
        response = {
            "base_submission_service_scope": submission_scope,
            "gcs_scope": gcs_scope.data_access,
            "full_scope": f"{submission_scope}[{gcs_scope.data_access}]",
        }
        self.finish(json.dumps(response))


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
    * session_required_mfa -- Is multi-factor-auth required?
    * prompt -- See docs.

    For more info, see the following:
    https://docs.globus.org/api/auth/sessions/#sessions-for-app-developers
    """

    supported_authorize_params = (
        "session_required_single_domain",
        "session_message",
        "session_required_identities",
        "session_required_mfa",
        "prompt",
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
            requested_scopes=self.get_query_argument(
                "requested_scopes", self.gconfig.get_scopes()
            ),
            refresh_tokens=self.gconfig.get_refresh_tokens(),
            prefill_named_grant=self.gconfig.get_named_grant(),
        )
        # Store the verifier, this is needed to complete the flow in the auth callback.
        self.store_verifier(verifier)

        # Set any custom Globus authorization parameters. Currently these are all session values
        authorize_params = {
            k: self.get_query_argument(k, None)
            for k in self.supported_authorize_params
            if self.get_query_argument(k, None)
        }
        self.log.debug(f"Using Authorize Params: {authorize_params}")
        authorize_url = client.oauth2_get_authorize_url(query_params=authorize_params)
        # Redirect the user to Globus Auth
        self.redirect(authorize_url)


class AuthCallbackManual(PKCEFlowManager):
    """
    This is a 'manual' callback handler for the last leg of the auth flow.

    The 'manual' comes from the user needing to automatically copy and paste
    the code into the JupyterLab environment. The code is copied into JupyterLab,
    then called in this routine to complete the flow.

    Direct browser access is not allowed, and will raise a warning in the logs.
    """

    @tornado.web.authenticated
    def get(self) -> Future:
        response = self.complete_auth_flow(self.get_query_argument("code"))
        self.finish(response.json())


class AuthCallback(RedirectWebHandler, PKCEFlowManager):
    @tornado.web.authenticated
    def get(self) -> Future:
        """
        This is an 'automatic' callback handler for the last leg of the auth flow.

        'automatic' means Globus Auth was able to redirect directly to this tornado
        backend endpoint to complete the flow, without user intervention. This can
        only be done for static urls, such as http://localhost:xxxx/globus-jupyterlab/oauth_callback

        Direct browser access is expected for the final auth redirect.
        """
        response = self.complete_auth_flow(self.get_query_argument("code"))
        self.finish(
            f"Thank you for logging in with Globus! You can close this page.\n"
            f"Status: {response.result}  {response.message}\n"
        )


class Logout(BaseAPIHandler):
    @tornado.web.authenticated
    def get(self):
        """
        Revoke all local Gloubs tokens
        """
        success = self.login_manager.logout()
        data = {
            "result": "success" if success else "failure",
            "details": "You have been logged out."
            if success
            else "You are not logged in!",
        }
        self.finish(json.dumps(data))


default_handlers = [
    ("/login", Login, dict(), "login"),
    ("/logout", Logout, dict(), "logout"),
    ("/oauth_callback", AuthCallback, dict(), "redirect_uri"),
    ("/oauth_callback_manual", AuthCallbackManual, dict(), "redirect_uri_manual"),
    (
        "/get_dependent_submission_scope",
        GetDependentSubmissionScope,
        dict(),
        "get_dependent_submission_scope",
    ),
]
