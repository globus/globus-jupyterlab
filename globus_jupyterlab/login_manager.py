import pathlib
from typing import Union
import logging
import globus_sdk
import globus_sdk.tokenstorage
import globus_sdk.scopes

from globus_jupyterlab.exc import TokenStorageError

log = logging.getLogger(__name__)


class LoginManager:

    storage_class = globus_sdk.tokenstorage.SimpleJSONFileAdapter
    storage_path = "~/.globus_jupyterlab_tokens.json"

    def __init__(self, client_id: str):
        self.client_id = client_id

        self.storage_path = pathlib.Path(self.storage_path).expanduser()
        self.storage = self.storage_class(str(self.storage_path))

    def store(self, token_response: globus_sdk.OAuthTokenResponse):
        self.storage.store(token_response)

    def is_logged_in(self) -> bool:
        return bool(self.storage.get_by_resource_server())

    def get_token_by_scope(self, scope: str) -> str:
        for token_data in self.storage.get_by_resource_server().values():
            if token_data["scope"] == scope:
                return token_data["access_token"]
        raise TokenStorageError(f"No valid token data for scope {scope}")

    def get_authorizer(
        self, resource_server: str
    ) -> Union[globus_sdk.AccessTokenAuthorizer, globus_sdk.RefreshTokenAuthorizer]:
        tokens = self.storage.get_token_data(resource_server)
        if tokens.get("refresh_token"):
            return globus_sdk.RefreshTokenAuthorizer(
                tokens["refresh_token"],
                globus_sdk.NativeAppAuthClient(self.client_id),
                access_token=tokens["access_token"],
                expires_at=tokens["access_token_expires"],
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
        try:
            self.storage_path.unlink()
        except FileNotFoundError:
            pass
        return tokens_revoked
