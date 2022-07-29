import pathlib
import pytest
import copy
from unittest.mock import Mock
import requests
import globus_sdk
from globus_sdk.tokenstorage import SimpleJSONFileAdapter
import base64
import pickle
import tornado.web

from globus_jupyterlab.handlers import get_handlers, HANDLER_MODULES
from globus_jupyterlab.handlers.base import BaseAPIHandler
from globus_jupyterlab.tests.mocks import (
    MockGlobusAPIError,
    MOCK_TOKENS,
    MOCK_IDENTITIES,
    SDKResponse,
    two_days_from_now_seconds,
)
from globus_jupyterlab.login_manager import LoginManager
from globus_jupyterlab.globus_config import GlobusConfig


@pytest.fixture
def app(token_storage, monkeypatch):
    monkeypatch.setattr(
        BaseAPIHandler.login_manager, "storage", token_storage("filename")
    )
    application = tornado.web.Application(get_handlers(HANDLER_MODULES, "/", ""))
    return application


@pytest.fixture
def logged_in(login_manager, token_storage) -> SimpleJSONFileAdapter:
    """Simulate a logged in Globus application"""
    token_storage.tokens = copy.deepcopy(MOCK_TOKENS)
    return token_storage


@pytest.fixture
def login_expired(logged_in) -> SimpleJSONFileAdapter:
    for token_data in logged_in.tokens.values():
        token_data["expires_at_seconds"] = 0
    return logged_in


@pytest.fixture
def login_refresh(logged_in) -> SimpleJSONFileAdapter:
    for token_data in logged_in.tokens.values():
        token_data["refresh_token"] = "mock_refresh_token"
    return logged_in


@pytest.fixture
def logged_out(token_storage) -> SimpleJSONFileAdapter:
    token_storage.tokens = {}
    return token_storage


@pytest.fixture
def logged_in_custom_transfer_service(monkeypatch, logged_in) -> SimpleJSONFileAdapter:
    logged_in.tokens["my_tokens"] = {
        "scope": "http://myscope",
        "access_token": "my_scope_access_token",
        "expires_at_seconds": two_days_from_now_seconds,
    }
    monkeypatch.setenv("GLOBUS_TRANSFER_SUBMISSION_URL", "https://myservice.gov")
    monkeypatch.setenv("GLOBUS_TRANSFER_SUBMISSION_SCOPE", "http://myscope")
    return logged_in


@pytest.fixture
def post_request(monkeypatch):
    "Mock the requests.post function, return the mock"

    class MockedPostResponse:
        data = {}
        status_code = 200

        def raise_for_status(self):
            if self.status_code == 500:
                response = Mock()
                response.status_code = 500
                raise requests.exceptions.HTTPError(response=response)

        def json(self):
            return self.data

    post = Mock(return_value=MockedPostResponse())
    monkeypatch.setattr(requests, "post", post)
    return post


@pytest.fixture
def gcp(monkeypatch) -> globus_sdk.LocalGlobusConnectPersonal:
    """Mock GCP, return the class instance"""
    # Set instance vars to return some mock values
    monkeypatch.setattr(globus_sdk, "LocalGlobusConnectPersonal", Mock())
    return globus_sdk.LocalGlobusConnectPersonal.return_value


@pytest.fixture
def sdk_error(monkeypatch) -> globus_sdk.GlobusAPIError:
    monkeypatch.setattr(globus_sdk, "GlobusAPIError", MockGlobusAPIError)
    return globus_sdk.GlobusAPIError


@pytest.fixture
def native_client(monkeypatch) -> globus_sdk.NativeAppAuthClient:
    monkeypatch.setattr(globus_sdk, "NativeAppAuthClient", Mock())
    return globus_sdk.NativeAppAuthClient.return_value


@pytest.fixture
def transfer_client(monkeypatch) -> globus_sdk.TransferClient:
    """Mock the tranfer client, return the class instance"""
    monkeypatch.setattr(globus_sdk, "TransferClient", Mock())
    inst = globus_sdk.TransferClient.return_value

    class MockData:
        data = {"mock_transfer": "data"}

    inst.submit_transfer.return_value = MockData()
    return inst


@pytest.fixture
def auth_client(monkeypatch) -> globus_sdk.AuthClient:
    """Mock the auth client, return the class instance"""
    monkeypatch.setattr(globus_sdk, "AuthClient", Mock())
    inst = globus_sdk.AuthClient.return_value
    inst.oauth2_userinfo.return_value = SDKResponse(data=MOCK_IDENTITIES)
    return globus_sdk.AuthClient.return_value


@pytest.fixture
def transfer_data(monkeypatch) -> globus_sdk.TransferClient:
    """Mock the tranfer data, return the class instance"""

    class MockTransferData:
        def __init__(self, tc, source, dest, label=None):
            self.data = {
                "source_endpoint": source,
                "destination_endpoint": dest,
                "label": label,
                "DATA": [],
            }

        def add_item(self, src, dest, recursive=False):
            self.data["DATA"].append((src, dest, recursive))

    monkeypatch.setattr(globus_sdk, "TransferData", MockTransferData)
    return globus_sdk.TransferData


@pytest.fixture
def oauthenticator(monkeypatch) -> dict:
    data = {"client_id": "client_uuid", "tokens": dict()}
    encoded_data = base64.b64encode(pickle.dumps(data))
    monkeypatch.setenv("GLOBUS_DATA", str(encoded_data))
    return data


@pytest.fixture()
def token_storage(monkeypatch) -> SimpleJSONFileAdapter:
    class MockStorage:
        tokens = {}

        def __init__(self, filename):
            pass

        def get_by_resource_server(self):
            return self.tokens

        def get_token_data(self, resource_server):
            return self.get_by_resource_server()[resource_server]

        def clear_tokens(self):
            MockStorage.tokens = {}

        on_refresh = Mock()
        store = Mock()

    storage = MockStorage
    monkeypatch.setattr(pathlib.Path, "unlink", MockStorage.clear_tokens)
    return storage


@pytest.fixture
def login_manager(monkeypatch, token_storage, login_manager_mocked_storage_check):
    monkeypatch.setattr(LoginManager, "storage_class", token_storage)
    return LoginManager("mock_client_id", pathlib.Path("/mock/path"))


@pytest.fixture
def login_manager_mocked_storage_check(monkeypatch):
    monkeypatch.setattr(LoginManager, "check_storage_path", Mock())
    return LoginManager.check_storage_path


@pytest.fixture(autouse=True)
def pathlib_unlink(monkeypatch):
    monkeypatch.setattr(pathlib.Path, "unlink", Mock())
    return pathlib.Path.unlink


@pytest.fixture()
def mock_hub_env(monkeypatch):
    """JupyterLab uses these env values to determine if it's in a 'hub' and not a local user machine"""
    monkeypatch.setenv("JUPYTERHUB_USER", "jovyan")
    monkeypatch.setenv("JUPYTERHUB_API_TOKEN", "mock_jupyterhub_api_token")
