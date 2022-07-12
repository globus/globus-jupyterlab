import pytest
from globus_jupyterlab.globus_config import GlobusConfig


def test_get_hub_token(monkeypatch):
    monkeypatch.setenv("JUPYTERHUB_API_TOKEN", "i_am_a_token!")
    assert GlobusConfig().get_hub_token() == "i_am_a_token!"


def test_get_gcp_collection(gcp):
    gcp.endpoint_id = "my_endpoint"
    assert GlobusConfig().get_gcp_collection() == "my_endpoint"
    assert GlobusConfig().get_collection_id() == "my_endpoint"
    assert GlobusConfig().is_gcp() is True


def test_non_gcp_collection(monkeypatch, gcp):
    monkeypatch.setenv("GLOBUS_COLLECTION_ID", "i_am_a_token!")
    gcp.endpoint_id = "my_endpoint"
    assert GlobusConfig().is_gcp() is False


@pytest.mark.parametrize(
    "case, default, env_value, expected",
    [
        (
            "Env correctly set to True, defalut is true, True expected",
            True,
            "true",
            True,
        ),
        (
            "Env set to True, defalut is False, false expected",
            True,
            "false",
            False,
        ),
        ("No value provided, default is True, True Expected", True, "", True),
        (
            "No value provided, default is True. False Expected",
            False,
            "",
            False,
        ),
        (
            "Env set to fruitloops, default is False. ValueError Exception Expected",
            False,
            "fruitloops",
            ValueError,
        ),
        (
            "Env set to coacoa puffs, default is true. ValueError Exception Expected",
            True,
            "coacoa puffs",
            ValueError,
        ),
    ],
)
def test_check_env_boolean(case, default, env_value, expected, monkeypatch):

    if env_value != "":
        monkeypatch.setenv("ENV_VALUE", env_value)
    if expected == ValueError:
        with pytest.raises(ValueError):
            GlobusConfig().check_env_boolean("ENV_VALUE", default)
    else:
        assert GlobusConfig().check_env_boolean("ENV_VALUE", default) == expected, case


def test_get_refresh_tokens(monkeypatch):
    monkeypatch.setenv("GLOBUS_REFRESH_TOKENS", "true")
    assert GlobusConfig().get_refresh_tokens() is True


def test_transfer_is_hub_service(monkeypatch):
    monkeypatch.setenv("GLOBUS_TRANSFER_SUBMISSION_IS_HUB_SERVICE", "true")
    assert GlobusConfig().get_transfer_submission_is_hub_service() is True


def test_get_last_login():
    gc = GlobusConfig()
    gc.last_login = "yesterday"
    assert gc.last_login == "yesterday"


def test_get_scopes():
    gc = GlobusConfig()
    assert gc.get_scopes() == [
        "urn:globus:auth:scope:transfer.api.globus.org:all",
        "profile",
        "openid",
    ]


def test_get_scopes_with_transfer(monkeypatch):
    monkeypatch.setenv("GLOBUS_TRANSFER_SUBMISSION_URL", "myservice")
    monkeypatch.setenv("GLOBUS_TRANSFER_SUBMISSION_SCOPE", "myscope")
    gc = GlobusConfig()
    assert gc.get_scopes() == [
        "urn:globus:auth:scope:transfer.api.globus.org:all",
        "profile",
        "openid",
        "myscope",
    ]


def test_get_named_grant_default():
    assert GlobusConfig().get_named_grant() == "Globus JupyterLab"


def test_set_custom_scope_without_url(monkeypatch):
    monkeypatch.setenv("GLOBUS_TRANSFER_SUBMISSION_SCOPE", "myscope")
    with pytest.raises(ValueError):
        GlobusConfig().get_transfer_submission_scope()


def test_get_redirect_uri(mock_hub_env):
    assert (
        GlobusConfig().get_redirect_uri() == "https://auth.globus.org/v2/web/auth-code"
    )


def test_gcp_owner_is_none(gcp):
    gcp.get_owner_info.return_value = None
    assert GlobusConfig().get_collection_id_owner() is None
