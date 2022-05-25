from unittest.mock import Mock
from urllib.parse import urlencode, urlparse, parse_qs
import json
import tornado
from globus_jupyterlab.tests.mocks import SDKResponse
import pytest


@pytest.mark.gen_test
@pytest.mark.parametrize(
    "operation, sdk_method, input, expected_status",
    [
        ("operation_ls", "operation_ls", {"endpoint": "foo"}, 200),
        ("operation_ls", "operation_ls", {"endpoint": "foo", "path": "bar"}, 200),
        ("operation_ls", "operation_ls", {}, 400),
        ("endpoint_search", "endpoint_search", {}, 200),
        ("endpoint_detail", "get_endpoint", {"endpoint": "foo"}, 200),
        ("endpoint_detail", "get_endpoint", {}, 400),
    ],
)
def test_get_api(
    operation,
    sdk_method,
    input,
    expected_status,
    http_client,
    base_url,
    transfer_client,
    logged_in,
):
    setattr(transfer_client, sdk_method, Mock(return_value=SDKResponse()))
    if expected_status >= 400:
        with pytest.raises(tornado.httpclient.HTTPClientError) as http_client_error:
            yield http_client.fetch(base_url + f"/{operation}?{urlencode(input)}")
        # This seems to be the best way to assert the status code response from tornado. It isn't ideal,
        # But it should be accurate
        assert f"HTTP {expected_status}" in str(http_client_error)
    else:
        response = yield http_client.fetch(
            base_url + f"/{operation}?{urlencode(input)}"
        )
        assert response.code == 200


@pytest.mark.gen_test
def test_401_login_url(http_client, base_url, transfer_client, sdk_error, logged_in):
    transfer_client.operation_ls.side_effect = sdk_error("401 error!", http_status=401)
    response = yield http_client.fetch(
        base_url + f"/operation_ls?endpoint=foo", raise_error=False
    )
    error = json.loads(response.body.decode("utf-8"))
    assert "login_url" in error

    login_url_p = urlparse(error["login_url"])
    query_params = parse_qs(login_url_p.query)

    assert login_url_p.path == "/login"
    assert "requested_scopes" in query_params
    assert query_params["requested_scopes"][0].startswith(
        "urn:globus:auth:scope:transfer.api.globus.org:all"
    )


@pytest.mark.gen_test
def test_401_login_url_non_gcs(
    http_client, base_url, transfer_client, sdk_error, logged_in
):
    """
    Test a call which isn't specific to a GCS endpoint, and uses base login scopes
    """
    transfer_client.endpoint_search.side_effect = sdk_error(
        "401 error!", http_status=401
    )
    response = yield http_client.fetch(
        base_url + f"/endpoint_search", raise_error=False
    )
    error = json.loads(response.body.decode("utf-8"))
    assert "login_url" in error


@pytest.mark.gen_test
def test_401_login_url_with_custom_submission_scope(
    http_client, base_url, transfer_client, sdk_error, monkeypatch, logged_in
):
    monkeypatch.setenv("GLOBUS_TRANSFER_SUBMISSION_URL", "https://myservice.gov")
    monkeypatch.setenv("GLOBUS_TRANSFER_SUBMISSION_SCOPE", "http://myscope")

    transfer_client.operation_ls.side_effect = sdk_error(
        "Need data_access scope!!", http_status=403, code="ConsentRequired"
    )
    response = yield http_client.fetch(
        base_url + f"/operation_ls?endpoint=foo", raise_error=False
    )
    error = json.loads(response.body.decode("utf-8"))
    query_params = parse_qs(urlparse(error["login_url"]).query)
    requested_scopes = query_params["requested_scopes"][0]

    assert query_params["requested_scopes"][0].startswith(
        "urn:globus:auth:scope:transfer.api.globus.org:all"
    )
    assert (
        "http://myscope[https://auth.globus.org/scopes/foo/data_access]"
        in requested_scopes
    )


@pytest.mark.gen_test
def test_transfer_submission_normal(
    http_client, base_url, transfer_client, transfer_data, sdk_error, logged_in
):
    body = json.dumps(
        {"source_endpoint": "mysource", "destination_endpoint": "mydest", "DATA": []}
    )
    response = yield http_client.fetch(
        base_url + f"/submit_transfer", raise_error=False, method="POST", body=body
    )
    assert response.code == 200


@pytest.mark.gen_test
def test_401_transfer_submission_normal(
    http_client, base_url, transfer_client, transfer_data, sdk_error, logged_in
):
    transfer_client.submit_transfer.side_effect = sdk_error(
        "401 error!", http_status=401
    )
    body = json.dumps(
        {"source_endpoint": "mysource", "destination_endpoint": "mydest", "DATA": []}
    )
    response = yield http_client.fetch(
        base_url + f"/submit_transfer", raise_error=False, method="POST", body=body
    )
    error = json.loads(response.body.decode("utf-8"))
    assert "login_url" in error
