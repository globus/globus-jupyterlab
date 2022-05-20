import pytest
from unittest.mock import Mock
import globus_sdk
from globus_sdk.tokenstorage import SimpleJSONFileAdapter
import base64
import pickle
import tornado.web

from globus_jupyterlab.handlers import get_handlers, HANDLER_MODULES
from globus_jupyterlab.tests.mocks import MockGlobusAPIError, MOCK_TOKENS
from globus_jupyterlab.login_manager import LoginManager
from globus_jupyterlab.globus_config import GlobusConfig

application = tornado.web.Application(get_handlers(HANDLER_MODULES, "/", ""))


@pytest.fixture
def app():
    return application


@pytest.fixture
def logged_in(token_storage) -> SimpleJSONFileAdapter:
    """Simulate a logged in Globus application"""
    token_storage.get_by_resource_server.return_value = MOCK_TOKENS
    return SimpleJSONFileAdapter


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
def transfer_client(monkeypatch) -> globus_sdk.TransferClient:
    """Mock the tranfer client, return the class instance"""
    monkeypatch.setattr(globus_sdk, "TransferClient", Mock())
    return globus_sdk.TransferClient.return_value


@pytest.fixture
def oauthenticator(monkeypatch) -> dict:
    data = {"client_id": "client_uuid", "tokens": dict()}
    encoded_data = base64.b64encode(pickle.dumps(data))
    monkeypatch.setenv("GLOBUS_DATA", str(encoded_data))
    return data


@pytest.fixture(autouse=True)
def token_storage(monkeypatch) -> SimpleJSONFileAdapter:
    monkeypatch.setattr(SimpleJSONFileAdapter, "store", Mock())
    monkeypatch.setattr(
        SimpleJSONFileAdapter, "get_by_resource_server", Mock(return_value={})
    )
    return SimpleJSONFileAdapter
