
from unittest import mock
import pytest
import os
from unittest.mock import Mock
import globus_sdk
import base64
import pickle
import tornado.web


from globus_jupyterlab.handlers import get_handlers, HANDLER_MODULES

application = tornado.web.Application(get_handlers(HANDLER_MODULES, '/', ''))


@pytest.fixture
def app():
    return application


@pytest.fixture
def mock_gcp(monkeypatch) -> Mock:
    gcp = Mock()
    # Set instance vars to return some mock values
    monkeypatch.setattr(globus_sdk, 'LocalGlobusConnectPersonal', Mock())
    return globus_sdk.LocalGlobusConnectPersonal.return_value


@pytest.fixture
def mock_oauthenticator(monkeypatch) -> Mock:
    data = {'client_id': 'client_uuid', 'tokens': dict()}
    encoded_data = base64.b64encode(pickle.dumps(data))
    monkeypatch.setenv('GLOBUS_DATA', str(encoded_data))
    return data
