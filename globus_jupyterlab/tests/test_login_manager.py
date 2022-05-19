import pytest
from unittest.mock import Mock
import pathlib
from globus_jupyterlab.login_manager import LoginManager
from globus_sdk.tokenstorage import SimpleJSONFileAdapter
import globus_sdk


def test_login_manager_logged_in(logged_in):
    lm = LoginManager("client_id")
    assert lm.is_logged_in() is True


def test_login_manager_logged_out(logged_out):
    lm = LoginManager("client_id")
    assert lm.is_logged_in() is False


def test_login_manager_tokens_expried(login_expired):
    lm = LoginManager("client_id")
    assert lm.is_logged_in() is False


def test_login_manager_refreshes_token(login_expired, login_refresh, monkeypatch):
    monkeypatch.setattr(globus_sdk.RefreshTokenAuthorizer, "ensure_valid_token", Mock())
    LoginManager("client_id")
    assert globus_sdk.RefreshTokenAuthorizer.ensure_valid_token.called


def test_login_manager_clears_tokens_on_failed_refresh(
    login_expired, login_refresh, monkeypatch
):
    monkeypatch.setattr(globus_sdk, "AuthAPIError", Exception)
    monkeypatch.setattr(
        globus_sdk.RefreshTokenAuthorizer,
        "ensure_valid_token",
        Mock(side_effect=globus_sdk.AuthAPIError),
    )
    monkeypatch.setattr(LoginManager, "clear_tokens", Mock())
    LoginManager("client_id")
    assert LoginManager.clear_tokens.called


def test_login_manager_clear_tokens(monkeypatch):
    monkeypatch.setattr(pathlib.Path, "unlink", Mock())
    LoginManager("client_id").clear_tokens()
    assert pathlib.Path.unlink.called


def test_login_manager_no_tokens_file(monkeypatch):
    monkeypatch.setattr(pathlib.Path, "unlink", Mock(side_effect=FileNotFoundError))
    LoginManager("client_id").clear_tokens()
    assert pathlib.Path.unlink.called


def test_login_manager_store_tokens(monkeypatch):
    monkeypatch.setattr(SimpleJSONFileAdapter, "store", Mock())
    LoginManager("client_id").store({})
    assert SimpleJSONFileAdapter.store.called


def test_login_manager_revoke_tokens(monkeypatch, logged_in, login_refresh):
    # Use refresh to simulate also revoking refresh tokens. It doesn't matter if
    # the access_tokens are expired
    monkeypatch.setattr(globus_sdk.NativeAppAuthClient, "oauth2_revoke_token", Mock())
    LoginManager("client_id").logout()
    num_tokens = len(login_refresh.tokens) * 2
    assert globus_sdk.NativeAppAuthClient.oauth2_revoke_token.call_count == num_tokens


def test_login_manager_apply_dependent_scopes():
    s = LoginManager("client_id").apply_dependent_scopes("foo", ["bar", "baz"])
    assert s == "foo[bar baz]"


def test_login_manager_apply_dependent_scopes_twice_error():
    with pytest.raises(ValueError):
        LoginManager("client_id").apply_dependent_scopes("foo[bar]", ["baz"])
