import pathlib
from typing import Union, List
import time
import logging
import globus_sdk
import globus_sdk.tokenstorage
import globus_sdk.scopes

log = logging.getLogger(__name__)


class LoginManager:

    storage_class = globus_sdk.tokenstorage.SimpleJSONFileAdapter
    storage_path = "~/.globus_jupyterlab_tokens.json"

    def __init__(self, client_id: str):
        self.client_id = client_id

        self.storage_path = pathlib.Path(self.storage_path).expanduser()
        self.storage = self.storage_class(str(self.storage_path))
        self.churn_tokens()

    def store(self, token_response: globus_sdk.OAuthTokenResponse):
        self.storage.store(token_response)

    def is_logged_in(self) -> bool:
        self.churn_tokens()
        return bool(self.storage.get_by_resource_server())

    def clear_tokens(self):
        """Clear all tokens from token storage. Logout should be called
        before this if tokens are still active."""
        try:
            self.storage_path.unlink()
        except FileNotFoundError:
            pass

    def is_valid_token(self, token_data) -> bool:
        expires_at = token_data.get("expires_at_seconds", 0)
        if time.time() <= expires_at:
            return True
        return False

    def churn_tokens(self):
        """Check for expired tokens and remove them from token storage. If tokens
        have a refresh token, refresh it."""
        for (
            resource_server,
            token_data,
        ) in self.storage.get_by_resource_server().items():
            authorizer = self.get_authorizer(resource_server)
            if isinstance(authorizer, globus_sdk.RefreshTokenAuthorizer):
                try:
                    authorizer.ensure_valid_token()
                except globus_sdk.AuthAPIError:
                    log.error("Tokens could not be refreshed, purging token store")
                    self.clear_tokens()
                    return
            else:
                if not self.is_valid_token(token_data):
                    log.info("Tokens have expired, you will need to login again")
                    self.clear_tokens()
                    return

    def get_authorizer(
        self, resource_server: str
    ) -> Union[globus_sdk.AccessTokenAuthorizer, globus_sdk.RefreshTokenAuthorizer]:
        tokens = self.storage.get_token_data(resource_server)
        if tokens.get("refresh_token"):
            return globus_sdk.RefreshTokenAuthorizer(
                tokens["refresh_token"],
                globus_sdk.NativeAppAuthClient(self.client_id),
                access_token=tokens["access_token"],
                expires_at=tokens["expires_at_seconds"],
                on_refresh=self.storage.on_refresh,
            )
        else:
            return globus_sdk.AccessTokenAuthorizer(tokens["access_token"])

    def logout(self) -> bool:
        """Revoke user tokens and clear them from storage. Returns true if tokens were revoked"""
        tokens_revoked = False
        client = globus_sdk.NativeAppAuthClient(self.client_id)
        for resource_server, data in self.storage.get_by_resource_server().items():
            log.debug(f"Revoking tokens for {resource_server}")
            tokens_revoked = True
            client.oauth2_revoke_token(data["access_token"])
            if data.get("refresh_token"):
                client.oauth2_revoke_token(data["refresh_token"])
        self.clear_tokens()
        return tokens_revoked

    @staticmethod
    def apply_dependent_scopes(base_scope: str, dependent_scopes: List[str]):
        """
        Given a base scope, include additional dependent scopes for downstream
        services. The most common usage is adding a GCS v5.4 data_access scope for
        ls/info/transfer operations.

        WARNING: Does not support multiple calls, doing so will result in an invalid
        scope.
        """
        if any(char in base_scope for char in "[ ]"):
            raise ValueError(
                f"Cannot extend additional dependent scopes on scope {base_scope}"
            )
        dep_scope_str = " ".join(dependent_scopes)
        return f"{base_scope}[{dep_scope_str}]"
