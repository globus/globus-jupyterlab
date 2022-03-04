import json
import pytest


@pytest.mark.gen_test
def test_config_with_gcp_environment(http_client, base_url, mock_gcp):
    mock_gcp.endpoint_id = 'my_gcp_id'
    mock_gcp.get_owner_info.return_value.id = 'owner_uuid'
    response = yield http_client.fetch(base_url + '/config')
    assert response.code == 200
    data = json.loads(response.body)
    assert data['collection_id'] == 'my_gcp_id'
    assert data['collection_id_owner'] == 'owner_uuid'
    assert data['is_gcp'] is True


@pytest.mark.gen_test
def test_config_with_hub_environment(http_client, base_url, mock_gcp, mock_oauthenticator):
    mock_gcp.endpoint_id = None
    mock_gcp.get_owner_info.return_value.id = None

    response = yield http_client.fetch(base_url + '/config')
    data = json.loads(response.body)
    assert response.code == 200
    assert data['is_gcp'] is False
