from globus_jupyterlab.globus_config import GlobusConfig


def test_get_hub_token(monkeypatch):
    monkeypatch.setenv('JUPYTERHUB_API_TOKEN', 'i_am_a_token!')
    assert GlobusConfig().get_hub_token() == 'i_am_a_token!'
