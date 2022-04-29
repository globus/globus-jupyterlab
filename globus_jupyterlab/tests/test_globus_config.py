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
