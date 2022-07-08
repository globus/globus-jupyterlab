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
