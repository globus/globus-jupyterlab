import pytest
from unittest.mock import Mock
import pathlib
from globus_jupyterlab.login_manager import LoginManager
from globus_sdk.tokenstorage import SimpleJSONFileAdapter
from globus_jupyterlab.exc import TokenStorageError
import globus_sdk


def test_login_manager_logged_in(logged_in, login_manager):
    assert login_manager.is_logged_in() is True


def test_login_manager_logged_out(logged_out, login_manager):
    assert login_manager.is_logged_in() is False


def test_login_manager_tokens_expried(login_expired, login_manager):
    assert login_manager.is_logged_in() is False


def test_login_manager_refreshes_token(
    login_expired, login_refresh, monkeypatch, login_manager
):
    monkeypatch.setattr(globus_sdk.RefreshTokenAuthorizer, "ensure_valid_token", Mock())
    LoginManager("client_id", pathlib.Path("/foo/bar/mytokens.json"))
    assert globus_sdk.RefreshTokenAuthorizer.ensure_valid_token.called


def test_login_manager_clears_tokens_on_failed_refresh(
    login_expired, login_refresh, monkeypatch, login_manager
):
    monkeypatch.setattr(globus_sdk, "AuthAPIError", Exception)
    monkeypatch.setattr(
        globus_sdk.RefreshTokenAuthorizer,
        "ensure_valid_token",
        Mock(side_effect=globus_sdk.AuthAPIError),
    )
    monkeypatch.setattr(LoginManager, "clear_tokens", Mock())
    LoginManager("client_id", pathlib.Path("/foo/bar/mytokens.json"))
    assert LoginManager.clear_tokens.called


def test_login_manager_clear_tokens(pathlib_unlink, login_manager_mocked_storage_check):
    LoginManager("client_id", pathlib.Path("/foo/bar/mytokens.json")).clear_tokens()
    assert pathlib_unlink.called


def test_login_manager_no_tokens_file(
    pathlib_unlink, login_manager_mocked_storage_check
):
    pathlib_unlink.side_effect = FileNotFoundError
    LoginManager("client_id", pathlib.Path("/foo/bar/mytokens.json")).clear_tokens()
    assert pathlib_unlink.called


def test_login_manager_store_tokens(monkeypatch, login_manager_mocked_storage_check):
    monkeypatch.setattr(SimpleJSONFileAdapter, "store", Mock())
    LoginManager("client_id", pathlib.Path("/foo/bar/mytokens.json")).store({})
    assert SimpleJSONFileAdapter.store.called


def test_login_manager_revoke_tokens(
    native_client, logged_in, login_refresh, login_manager
):
    # Use refresh to simulate also revoking refresh tokens. It doesn't matter if
    # the access_tokens are expired
    # monkeypatch.setattr(globus_sdk.NativeAppAuthClient, "oauth2_revoke_token", Mock())
    num_tokens = len(login_refresh.tokens) * 2
    login_manager.logout()
    assert native_client.oauth2_revoke_token.call_count == num_tokens


def test_login_manager_logout_clears_tokens(
    native_client, pathlib_unlink, login_manager_mocked_storage_check
):
    LoginManager("client_id", pathlib.Path("/foo/bar/mytokens.json")).logout()
    assert pathlib_unlink.called


def test_login_manager_apply_dependent_scopes(login_manager):
    s = login_manager.apply_dependent_scopes("foo", ["bar", "baz"])
    assert s == "foo[bar baz]"


def test_login_manager_apply_dependent_scopes_twice_error(login_manager):
    with pytest.raises(ValueError):
        login_manager.apply_dependent_scopes("foo[bar]", ["baz"])


def test_login_manager_invalid_path():
    with pytest.raises(TokenStorageError):
        LoginManager("client_id", pathlib.Path(""))
