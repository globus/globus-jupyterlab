import json
import pytest


@pytest.mark.gen_test
def test_config_logged_out(http_client, base_url, logged_out):
    response = yield http_client.fetch(base_url + "/config")
    data = json.loads(response.body)
    assert response.code == 200
    assert data["is_logged_in"] is False


@pytest.mark.gen_test
def test_config_tokens_expired_log_out_user(http_client, base_url, login_expired):
    response = yield http_client.fetch(base_url + "/config")
    data = json.loads(response.body)
    assert response.code == 200
    assert data["is_logged_in"] is False


@pytest.mark.gen_test
def test_config_logged_in(http_client, base_url, logged_in):
    response = yield http_client.fetch(base_url + "/config")
    data = json.loads(response.body)
    assert response.code == 200
    assert data["is_logged_in"] is True


@pytest.mark.gen_test
def test_config_with_gcp_environment(http_client, base_url, gcp):
    gcp.endpoint_id = "my_gcp_id"
    gcp.get_owner_info.return_value.id = "owner_uuid"
    response = yield http_client.fetch(base_url + "/config")
    assert response.code == 200
    data = json.loads(response.body)
    assert data["collection_id"] == "my_gcp_id"
    assert data["collection_id_owner"] == "owner_uuid"
    assert data["is_gcp"] is True


@pytest.mark.gen_test
def test_config_with_hub_environment(http_client, base_url, gcp, oauthenticator):
    gcp.endpoint_id = None
    gcp.get_owner_info.return_value.id = None

    response = yield http_client.fetch(base_url + "/config")
    data = json.loads(response.body)
    assert response.code == 200
    assert data["is_gcp"] is False
