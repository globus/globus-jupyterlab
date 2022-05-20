import json
import re
import logging
import urllib
import tornado
import globus_sdk
import pydantic
import requests
from typing import List
from globus_jupyterlab.exc import LoginException
from globus_jupyterlab.handlers.base import BaseAPIHandler
from globus_jupyterlab.models import TransferModel


class AutoAuthURLMixin(BaseAPIHandler):
    login_checks = [
        "check_login_required",
    ]

    def is_login_required(self, exception: globus_sdk.GlobusAPIError) -> bool:
        """
        Check if the exception requries login. For normal calls to services, this just
        means a 401, but there are a slew of possible login cases for GCS.
        """
        for func_name in self.login_checks:
            check = getattr(self, func_name)
            check_result = check(exception)
            self.log.debug(f"Checking exception was due to {func_name}: {check_result}")
            if check_result:
                return True
        return False

    def check_login_required(self, exception: globus_sdk.GlobusAPIError):
        return exception.http_status == 401

    def get_requested_scopes(self, exception: globus_sdk.GlobusAPIError) -> List[str]:
        return self.gconfig.get_scopes()

    def get_required_session_domains(
        self, exception: globus_sdk.GlobusAPIError
    ) -> List[str]:
        return []

    def get_globus_login_url(self, exception: globus_sdk.GlobusAPIError) -> str:
        login_url = self.reverse_url("login")
        domain = ",".join(self.get_required_session_domains(exception))
        params = dict(
            requested_scopes=" ".join(self.get_requested_scopes(exception)),
        )
        domains = self.get_required_session_domains(exception)
        if domains:
            params["session_required_single_domain"] = domains[0]

        full_login_url = f"{login_url}?{urllib.parse.urlencode(params)}"
        self.log.debug(f"Generated login url: {full_login_url}")
        return full_login_url


class GCSAuthMixin(AutoAuthURLMixin):
    """Mixin for handling 403 responses from querying a Globus Connect Server which
    requries the data_access scope. This mixin will introspect the query params for
    the collection using `gcs_query_param`. This value needs to match the expected
    gcs query param or the request will fail.

    For 403 responses, responses will include a login urls with the extended scopes
    for the data_access scope, for each `base_scope` defined below (by default it
    is only transfer) Additionally, if a custom transfer submission scope is used,
    that will also be automatically requested."""

    gcs_query_param = "endpoint"
    login_checks = [
        "check_login_required",
        "check_gcsv4_requires_activation",
        "check_gcsv54_consent_data_access",
        "check_gcsv54_ha_not_from_allowed_domain",
    ]

    def get_globus_login_url(self, exception: globus_sdk.GlobusAPIError):
        if self.check_gcsv4_requires_activation(exception):
            endpoint = self.get_query_argument(self.gcs_query_param, None)
            return f"https://app.globus.org/file-manager?origin_id={endpoint}"
        return super().get_globus_login_url(exception)

    def check_gcsv4_requires_activation(
        self, exception: globus_sdk.GlobusAPIError
    ) -> bool:
        return (
            exception.http_status == 400
            and exception.code == "ClientError.ActivationRequired"
        )

    def check_gcsv54_ha_not_from_allowed_domain(
        self, exception: globus_sdk.GlobusAPIError
    ) -> bool:
        """
        High Assurance collection, a required session is missing.
        """
        if exception.http_status == 502:
            # TODO We could probably use pydantic to parse these responses into objects for easier
            # use.
            resp = self.parse_gridftp_json_response(exception.message)
            if (
                resp.get("detail", {}).get("DATA_TYPE")
                == "not_from_allowed_domain#1.0.0"
            ):
                return True
        return False

    def check_gcsv54_consent_data_access(
        self, exception: globus_sdk.GlobusAPIError
    ) -> bool:
        """
        Collection is a GCS v5.4 mapped collection and requires a data_access scope
        """
        return exception.http_status == 403 and exception.code == "ConsentRequired"

    def get_requested_scopes(self, exception: globus_sdk.GlobusAPIError):
        base_scopes = super().get_requested_scopes(exception)
        if self.check_gcsv54_consent_data_access(exception):
            collection = self.get_query_argument(self.gcs_query_param, None)
            if not collection:
                # This is a bug in Globus Jupyterlab, where the collection cannot be determined.
                raise LoginException(
                    "Could not determine the GCS collection which needs data_access."
                )
            dependent_scope = globus_sdk.scopes.GCSCollectionScopeBuilder(collection)
            requested_scopes = [
                self.login_manager.apply_dependent_scopes(
                    base, [dependent_scope.data_access]
                )
                for base in base_scopes
            ]
        else:
            requested_scopes = base_scopes
        self.log.debug(
            f"Generated Login URL with the following requested_scopes: {requested_scopes}"
        )
        return requested_scopes

    def get_required_session_domains(self, exception: globus_sdk.GlobusAPIError):
        if self.check_gcsv54_ha_not_from_allowed_domain(exception):
            domains = self.parse_gridftp_json_response(exception.message)["detail"][
                "allowed_domains"
            ]
            self.log.info(f"GCS EP Requires domains: {domains}")
            return domains
        return []

    def parse_gridftp_json_response(self, response) -> dict:
        try:
            match = re.search(r"530-GridFTP-JSON-Result: (.+)\\r\\n530 End", response)
            if match:
                return json.loads(match.groups()[0])
        except json.decoder.JSONDecodeError:
            # We got an error back from GridFTP, but it didn't match the expected format. This should
            # never happen and means the GridFTP has changed, and this package should be updated.
            self.log.error(
                "Found GridFTP error but failed to parse it. This is an error and needs to be fixed."
            )


class GlobusSDKWrapper(AutoAuthURLMixin):

    globus_sdk_method = None
    mandatory_args = []
    optional_args = {}

    def get_globus_sdk_args(self):
        return [], {}

    def sdk_wrapper_call(self):
        response = dict()
        if self.login_manager.is_logged_in() is not True:
            self.set_status(401)
            return self.finish(json.dumps({"error": "The user is not logged in"}))
        try:
            authorizer = self.login_manager.get_authorizer("transfer.api.globus.org")
            tc = globus_sdk.TransferClient(authorizer=authorizer)
            method = getattr(tc, self.globus_sdk_method)
            args, kwargs = self.get_globus_sdk_args()
            response = method(*args, **kwargs)
            return self.finish(json.dumps(response.data))
        except globus_sdk.GlobusAPIError as gapie:
            self.set_status(gapie.http_status)
            response = {"error": gapie.code, "details": gapie.message}
            if self.is_login_required(gapie):
                response["login_required"] = True
                try:
                    self.set_status(401)
                    response["login_url"] = self.get_globus_login_url(gapie)
                except LoginException as le:
                    self.log.error("Failed to generate login URL", exc_info=True)
                    response["error"] = le.__class__.__name__
                    response["details"] = str(le)
            from pprint import pprint

            pprint(response)
            return self.finish(json.dumps(response))


class GetMethodTransferAPIEndpoint(GlobusSDKWrapper):
    def get_globus_sdk_args(self):
        args = [self.get_query_argument(arg) for arg in self.mandatory_args]
        kwargs = {
            arg: self.get_query_argument(arg, default)
            for arg, default in self.optional_args.items()
        }
        return args, kwargs

    def get(self):
        self.sdk_wrapper_call()


class POSTMethodTransferAPIEndpoint(GlobusSDKWrapper):
    def get_globus_sdk_args(self):
        post_data = json.loads(self.request.body)
        try:
            args = [post_data.pop(arg) for arg in self.mandatory_args]
        except KeyError:
            msg = f'Minimum args not specified: {", ".join(self.mandatory_args)}'
            raise ValueError(msg) from None
        return args, post_data

    def post(self):
        try:
            self.sdk_wrapper_call()
        except ValueError as ve:
            self.set_status(400)
            self.finish(json.dumps({"code": "InvalidInput", "message": str(ve)}))


class EndpointAutoactivate(POSTMethodTransferAPIEndpoint):
    """An API Endpoint doing a Globus LS"""

    globus_sdk_method = "endpoint_autoactivate"
    mandatory_args = ["endpoint_id"]
    optional_args = {}


class SubmitTransfer(GCSAuthMixin):
    """An API Endpoint for submitting Globus Transfers."""

    @tornado.web.authenticated
    def post(self):
        """
        Attempt to submit a transfer with tokens previously loaded by a user.
        """
        response = dict()
        if self.login_manager.is_logged_in() is not True:
            self.set_status(401)
            return self.finish(json.dumps({"error": "The user is not logged in"}))
        try:
            post_data = json.loads(self.request.body)
            self.log.debug("Checking transfer document")
            tm = TransferModel(**post_data)
            if self.gconfig.get_transfer_submission_url():
                response = self.submit_custom_transfer(tm)
            else:
                response = self.submit_normal_transfer(tm)

            return self.finish(json.dumps(response))
        except pydantic.ValidationError as ve:
            self.set_status(400)
            self.log.debug("Transfer doc failed validation", exc_info=True)
            return self.finish(
                json.dumps({"error": "Invalid Input", "details": ve.json()})
            )
        except globus_sdk.GlobusAPIError as gapie:
            self.set_status(gapie.http_status)
            response = {"error": gapie.code, "details": gapie.message}
            if gapie.http_status in [401, 403]:
                response["login_url"] = self.get_globus_login_url()
            return self.finish(json.dumps(response))

    def submit_custom_transfer(self, transfer_data: TransferModel):
        url = self.gconfig.get_transfer_submission_url()
        scope = self.gconfig.get_transfer_submission_scope()
        try:
            globus_token = self.login_manager.get_token_by_scope(scope)
            if self.gconfig.get_transfer_submission_is_hub_service() is True:
                self.log.debug(
                    "Using hub token to authorize transfer submission request. This is "
                    "due to setting GLOBUS_TRANSFER_SUBMISSION_IS_HUB_SERVICE"
                )
                auth_token = self.gconfig.get_hub_token()
                post_data_token = globus_token
            else:
                auth_token = globus_token
                post_data_token = None

            headers = {"Authorization": f"Bearer {auth_token}"}
            document = {
                "globus_token": post_data_token,
                "transfer": transfer_data.dict(),
            }
            self.log.info(
                f"Submitting transfer request to custom location {url} "
                "Using Scope {scope}"
            )
            result = requests.post(url, headers=headers, json=document)
            result.raise_for_status()
            self.set_status(result.status_code)
            data = result.json()
            if "task_id" not in data:
                self.log.error(f"Response from {url} did not return a task ID!")
            data["task_id"] = None
            return data
        except requests.exceptions.HTTPError as http_error:
            self.set_status(503)
            self.log.error(
                f"Request failed with error code: {http_error.response.status_code}",
                exc_info=True,
            )
            return {"error": "Transfer Failed", "details": str(http_error)}

    def submit_normal_transfer(self, transfer_data: TransferModel):
        authorizer = self.login_manager.get_authorizer("transfer.api.globus.org")
        tc = globus_sdk.TransferClient(authorizer=authorizer)

        td = globus_sdk.TransferData(
            tc, transfer_data.source_endpoint, transfer_data.destination_endpoint
        )
        for transfer_item in transfer_data.DATA:
            td.add_item(
                transfer_item.source_path,
                transfer_item.destination_path,
                recursive=transfer_item.recursive,
            )
        return tc.submit_transfer(td).data


class OperationLS(GCSAuthMixin, GetMethodTransferAPIEndpoint):
    """An API Endpoint doing a Globus LS"""

    globus_sdk_method = "operation_ls"
    mandatory_args = ["endpoint"]
    optional_args = {"path": None, "show_hidden": 0}


class EndpointSearch(GetMethodTransferAPIEndpoint):
    """An API Endpoint for searching for collections"""

    globus_sdk_method = "endpoint_search"
    mandatory_args = []
    optional_args = {
        "filter_fulltext": None,
        "filter_scope": None,
        "filter_owner_id": None,
        "filter_host_endpoint": None,
        "filter_non_functional": False,
        "limit": 10,
        "offset": 0,
    }


class EndpointDetail(GCSAuthMixin, GetMethodTransferAPIEndpoint):
    globus_sdk_method = "get_endpoint"
    mandatory_args = ["endpoint"]
    optional_args = {}


default_handlers = [
    ("/submit_transfer", SubmitTransfer, dict(), "submit_transfer"),
    ("/operation_ls", OperationLS, dict(), "operation_ls"),
    ("/endpoint_search", EndpointSearch, dict(), "endpoint_search"),
    ("/endpoint_detail", EndpointDetail, dict(), "endpoint_detail"),
    ("/endpoint_autoactivate", EndpointAutoactivate, dict(), "endpoint_autoactivate"),
]
