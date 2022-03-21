import pathlib
from typing import Union
import logging
import globus_sdk
import globus_sdk.tokenstorage
import globus_sdk.scopes

log = logging.getLogger(__name__)


class LoginManager:

    storage_class = globus_sdk.tokenstorage.SimpleJSONFileAdapter
    storage_path = '~/.globus_jupyterlab_tokens.json'

    def __init__(self, client_id: str):
        self.client_id = client_id

        path = pathlib.Path(self.storage_path).expanduser()
        self.storage = self.storage_class(str(path))

    def store(self, token_response: globus_sdk.OAuthTokenResponse):
        self.storage.store(token_response)

    def is_logged_in(self) -> bool:
        return bool(self.storage.get_by_resource_server())

    def get_authorizer(self, resource_server: str) -> Union[globus_sdk.AccessTokenAuthorizer,
                                                            globus_sdk.RefreshTokenAuthorizer]:
        tokens = self.storage.get_token_data(resource_server)
        if tokens.get('refresh_token'):
            return globus_sdk.RefreshTokenAuthorizer(
                tokens['refresh_token'],
                globus_sdk.NativeAppAuthClient(self.client_id),
                access_token=tokens['access_token'],
                expires_at=tokens['access_token_expires'],
                on_refresh=self.storage.on_refresh,
            )
        else:
            return globus_sdk.AccessTokenAuthorizer()
