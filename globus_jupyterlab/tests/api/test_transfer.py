from unittest.mock import Mock
from urllib.parse import urlencode, urlparse, parse_qs
import json
import requests
import urllib
import tornado
from globus_jupyterlab.tests.mocks import (
    SDKResponse,
    GRIDFTP_HA_NOT_FROM_ALLOWED_DOMAIN,
    GRIDFTP_S3_CREDENTIALS_REQUIRED_MESSAGE,
    GRIDFTP_UNEXPECTED_MESSAGE,
)
import pytest
from globus_jupyterlab.handlers.api.transfer import SubmitTransfer


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
    response = yield http_client.fetch(
        base_url + f"/{operation}?{urlencode(input)}", raise_error=False
    )
    print(response.body.decode("utf-8"))
    assert response.code == expected_status


@pytest.mark.gen_test
@pytest.mark.parametrize(
    "grid_ftp_message, login_required, requires_user_intervention, login_url",
    [
        (
            GRIDFTP_HA_NOT_FROM_ALLOWED_DOMAIN,
            True,
            False,
            "/login?requested_scopes=urn%3Aglobus%3Aauth%3Ascope%3Atransfer.api.globus.org%3Aall&prompt=login&session_required_identities=7d4657a1-0422-409a-a0ee-077f4a6a99a1&session_message=The+collection+you+selected+requires+a+fresh+login",
        ),
        (
            GRIDFTP_S3_CREDENTIALS_REQUIRED_MESSAGE,
            False,
            True,
            "https://app.globus.org/file-manager?origin_id=Foo",
        ),
        (
            GRIDFTP_UNEXPECTED_MESSAGE,
            False,
            True,
            "https://app.globus.org/file-manager?origin_id=Foo",
        ),
    ],
)
def test_gridftp_login_errors(
    grid_ftp_message,
    login_required,
    requires_user_intervention,
    login_url,
    http_client,
    base_url,
    transfer_client,
    sdk_error,
    auth_client,
    logged_in,
):
    transfer_client.operation_ls.side_effect = sdk_error(
        grid_ftp_message,
        code="ExternalError.DirListingFailed.LoginFailed",
        http_status=502,
    )
    response = yield http_client.fetch(
        base_url + f"/operation_ls?endpoint=Foo", raise_error=False
    )
    assert response.code == 401
    error = json.loads(response.body.decode("utf-8"))
    assert error["login_required"] == login_required
    assert error["requires_user_intervention"] == requires_user_intervention
    response_login_url = urllib.parse.urlparse(error["login_url"])
    if response_login_url.netloc == "app.globus.org":
        assert error["login_url"] == login_url
    else:
        assert f"{response_login_url.path}?{response_login_url.query}" == login_url


@pytest.mark.gen_test
def test_400_unrelated(http_client, base_url, transfer_client, sdk_error, logged_in):
    transfer_client.operation_ls.side_effect = sdk_error("400 error!", http_status=400)
    response = yield http_client.fetch(
        base_url + f"/operation_ls?endpoint=", raise_error=False
    )
    assert response.code == 400


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

    # There should be only two scopes given data_access
    assert len(requested_scopes.split()) == 2

    assert query_params["requested_scopes"][0].startswith(
        "urn:globus:auth:scope:transfer.api.globus.org:all"
    )
    assert (
        "http://myscope[urn:globus:auth:scope:transfer.api.globus.org:all[https://auth.globus.org/scopes/foo/data_access]"
        in requested_scopes
    )


@pytest.mark.gen_test
def test_transfer_submission_normal(
    http_client, base_url, transfer_client, transfer_data, sdk_error, logged_in
):
    transfer_client.submit_transfer.return_value = SDKResponse(
        data={"task_id": "my_taks_id"}
    )
    body = json.dumps(
        {"source_endpoint": "mysource", "destination_endpoint": "mydest", "DATA": []}
    )
    response = yield http_client.fetch(
        base_url + f"/submit_transfer", raise_error=False, method="POST", body=body
    )
    assert response.code == 200
    data = json.loads(response.body.decode("utf-8"))
    assert "task_id" in data


@pytest.mark.gen_test
@pytest.mark.parametrize(
    "collection, globus_host_posix_basepath, globus_host_collection_basepath, transfer_doc, expected, case",
    [
        (
            "host_collection_uuid",
            "",
            "",
            {
                "source_endpoint": "host_collection_uuid",
                "destination_endpoint": "user_selected_collection",
                "DATA": [
                    {
                        "source_path": "foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
            ("foo.txt", "foo.txt", False),
            "Base case, no path translation",
        ),
        (
            "host_collection_uuid",
            "/home/jovyan/",
            "",
            {
                "source_endpoint": "host_collection_uuid",
                "destination_endpoint": "user_selected_collection",
                "DATA": [
                    {
                        "source_path": "/home/jovyan/foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
            ("foo.txt", "foo.txt", False),
            "Rationally configured environment",
        ),
        (
            "host_collection_uuid",
            "/home/jovyan",
            "",
            {
                "source_endpoint": "host_collection_uuid",
                "destination_endpoint": "user_selected_collection",
                "DATA": [
                    {
                        "source_path": "/home/jovyan/foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
            ("foo.txt", "foo.txt", False),
            "Missing Trailing Slash",
        ),
        (
            "host_collection_uuid",
            "/home/jovyan/",
            "",
            {
                "source_endpoint": "user_selected_collection",
                "destination_endpoint": "host_collection_uuid",
                "DATA": [
                    {
                        "source_path": "foo.txt",
                        "destination_path": "/home/jovyan/foo.txt",
                        "recursive": False,
                    }
                ],
            },
            ("foo.txt", "foo.txt", False),
            "Test Translating Destination",
        ),
        (
            "host_collection_uuid",
            "",
            "/shared",
            {
                "source_endpoint": "host_collection_uuid",
                "destination_endpoint": "user_selected_collection",
                "DATA": [
                    {
                        "source_path": "foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
            ("/shared/foo.txt", "foo.txt", False),
            "Test Collection Base Path",
        ),
        (
            "host_collection_uuid",
            "",
            "shared",
            {
                "source_endpoint": "host_collection_uuid",
                "destination_endpoint": "user_selected_collection",
                "DATA": [
                    {
                        "source_path": "foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
            ("shared/foo.txt", "foo.txt", False),
            "Test Relative Collection Base Path",
        ),
        (
            "host_collection_uuid",
            "/home/jovyan",
            "/shared",
            {
                "source_endpoint": "host_collection_uuid",
                "destination_endpoint": "user_selected_collection",
                "DATA": [
                    {
                        "source_path": "/home/jovyan/foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
            ("/shared/foo.txt", "foo.txt", False),
            "Test both posix basepath with collection basepath",
        ),
        (
            "host_collection_uuid",
            "/home/jovyan/",
            "/shared/",
            {
                "source_endpoint": "host_collection_uuid",
                "destination_endpoint": "user_selected_collection",
                "DATA": [
                    {
                        "source_path": "/home/jovyan/foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
            ("/shared/foo.txt", "foo.txt", False),
            "Test trailing slash",
        ),
        (
            "no_exist",
            "/home/jovyan/",
            "",
            {
                "source_endpoint": "some_other_collection",
                "destination_endpoint": "user_selected_collection",
                "DATA": [
                    {
                        "source_path": "foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
            500,
            "Test no hub collection for transfer",
        ),
        (
            "host_collection_uuid",
            "/home/jovyan/",
            "",
            {
                "source_endpoint": "host_collection_uuid",
                "destination_endpoint": "user_selected_collection",
                "DATA": [
                    {
                        "source_path": "/some/other/path/foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
            400,
            "Test transfer is outside share path",
        ),
    ],
)
def test_transfer_submission_with_posix_basepath(
    monkeypatch,
    collection,
    globus_host_posix_basepath,
    globus_host_collection_basepath,
    transfer_doc,
    expected,
    case,
    http_client,
    base_url,
    transfer_client,
    transfer_data,
    sdk_error,
    logged_in,
):
    monkeypatch.setenv("GLOBUS_COLLECTION_ID", collection)
    monkeypatch.setenv("GLOBUS_HOST_POSIX_BASEPATH", globus_host_posix_basepath)
    monkeypatch.setenv(
        "GLOBUS_HOST_COLLECTION_BASEPATH", globus_host_collection_basepath
    )
    transfer_client.submit_transfer.return_value = SDKResponse(
        data={"task_id": "my_taks_id"}
    )
    body = json.dumps(transfer_doc)
    response = yield http_client.fetch(
        base_url + f"/submit_transfer", raise_error=False, method="POST", body=body
    )
    print(f'Response {response.body.decode("utf-8")}')
    if isinstance(expected, int):
        assert response.code == expected
    else:
        # Fetch arg in submit_transfer(transfer_data)
        mock_transfer_data = transfer_client.submit_transfer.call_args[0][0]
        assert mock_transfer_data.data["DATA"] == [expected], case
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


@pytest.mark.gen_test
def test_401_transfer_submission_invalid_body(
    http_client, base_url, transfer_client, transfer_data, sdk_error, logged_in
):
    body = json.dumps({"src": "mysource", "destination_endpoint": "mydest", "DATA": []})
    response = yield http_client.fetch(
        base_url + f"/submit_transfer", raise_error=False, method="POST", body=body
    )
    assert response.code == 400


@pytest.mark.gen_test
def test_transfer_submission_custom_valid_non_hub_service(
    http_client,
    base_url,
    transfer_client,
    sdk_error,
    monkeypatch,
    post_request,
    logged_in_custom_transfer_service,
    mock_hub_env,
):
    monkeypatch.setenv("GLOBUS_COLLECTION_ID", "mysource")
    post_request.return_value.data = {"task_id": "my_task_id"}

    transfer_client.submit_transfer.return_value = SDKResponse(
        data={"task_id": "my_taks_id"}
    )
    body = json.dumps(
        {
            "source_endpoint": "mysource",
            "destination_endpoint": "mydest",
            "DATA": [
                {
                    "source_path": "foo.txt",
                    "destination_path": "foo.txt",
                    "recursive": False,
                }
            ],
        }
    )
    response = yield http_client.fetch(
        base_url + f"/submit_transfer", raise_error=False, method="POST", body=body
    )
    assert response.code == 200
    data = json.loads(response.body.decode("utf-8"))
    assert data == {"task_id": "my_task_id"}
    post_request.assert_called_with(
        "https://myservice.gov",
        headers={"Authorization": "Bearer my_scope_access_token"},
        json={
            "globus_token": None,
            "transfer": {
                "source_endpoint": "mysource",
                "destination_endpoint": "mydest",
                "label": None,
                "DATA": [
                    {
                        "source_path": "foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
        },
    )


@pytest.mark.gen_test
def test_transfer_submission_custom_valid_hub_service(
    http_client,
    base_url,
    transfer_client,
    sdk_error,
    monkeypatch,
    post_request,
    logged_in_custom_transfer_service,
    mock_hub_env,
):

    monkeypatch.setenv("GLOBUS_COLLECTION_ID", "mysource")
    monkeypatch.setenv("GLOBUS_TRANSFER_SUBMISSION_IS_HUB_SERVICE", "true")
    post_request.return_value.data = {"task_id": "my_task_id"}

    transfer_client.submit_transfer.return_value = SDKResponse(
        data={"task_id": "my_taks_id"}
    )
    body = json.dumps(
        {
            "source_endpoint": "mysource",
            "destination_endpoint": "mydest",
            "DATA": [
                {
                    "source_path": "foo.txt",
                    "destination_path": "foo.txt",
                    "recursive": False,
                }
            ],
        }
    )
    response = yield http_client.fetch(
        base_url + f"/submit_transfer", raise_error=False, method="POST", body=body
    )
    assert response.code == 200
    data = json.loads(response.body.decode("utf-8"))
    assert data == {"task_id": "my_task_id"}
    post_request.assert_called_with(
        "https://myservice.gov",
        headers={"Authorization": "Bearer mock_jupyterhub_api_token"},
        json={
            "globus_token": "my_scope_access_token",
            "transfer": {
                "source_endpoint": "mysource",
                "destination_endpoint": "mydest",
                "label": None,
                "DATA": [
                    {
                        "source_path": "foo.txt",
                        "destination_path": "foo.txt",
                        "recursive": False,
                    }
                ],
            },
        },
    )


@pytest.mark.gen_test
def test_transfer_submission_custom_no_task_id_returned(
    http_client,
    base_url,
    transfer_client,
    sdk_error,
    monkeypatch,
    post_request,
    logged_in_custom_transfer_service,
    mock_hub_env,
):
    post_request.return_value.data = {}

    transfer_client.submit_transfer.return_value = SDKResponse(
        data={"task_id": "my_taks_id"}
    )
    body = json.dumps(
        {"source_endpoint": "mysource", "destination_endpoint": "mydest", "DATA": []}
    )
    response = yield http_client.fetch(
        base_url + f"/submit_transfer", raise_error=False, method="POST", body=body
    )
    assert response.code == 200
    data = json.loads(response.body.decode("utf-8"))
    assert data == {"task_id": None}


@pytest.mark.gen_test
def test_transfer_submission_custom_resource_server_error(
    http_client,
    base_url,
    transfer_client,
    sdk_error,
    monkeypatch,
    post_request,
    logged_in_custom_transfer_service,
    mock_hub_env,
):
    post_request.return_value.status_code = 500

    transfer_client.submit_transfer.return_value = SDKResponse(
        data={"task_id": "my_taks_id"}
    )
    body = json.dumps(
        {"source_endpoint": "mysource", "destination_endpoint": "mydest", "DATA": []}
    )
    response = yield http_client.fetch(
        base_url + f"/submit_transfer", raise_error=False, method="POST", body=body
    )
    assert response.code == 503
