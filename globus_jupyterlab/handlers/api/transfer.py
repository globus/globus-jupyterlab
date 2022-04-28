import json
import urllib
import tornado
import globus_sdk
import pydantic
import requests
from globus_jupyterlab.exc import TokenStorageError
from globus_jupyterlab.handlers.base import BaseAPIHandler
from globus_jupyterlab.models import TransferModel


class GCSAuthMixin(BaseAPIHandler):
    """Mixin for handling 403 responses from querying a Globus Connect Server which
    requries the data_access scope. This mixin will introspect the query params for
    the collection using `gcs_query_param`. This value needs to match the expected
    gcs query param or the request will fail.

    For 403 responses, responses will include a login urls with the extended scopes
    for the data_access scope, for each `base_scope` defined below (by default it
    is only transfer) Additionally, if a custom transfer submission scope is used,
    that will also be automatically requested."""

    gcs_query_param = "endpoint"
    base_scopes = [globus_sdk.scopes.TransferScopes.all]

    def get_requested_scopes(self):
        collection = self.get_query_argument(self.gcs_query_param)
        gcs_scope = globus_sdk.scopes.GCSCollectionScopeBuilder(collection)
        requested_scopes = [
            f"{base_scope}[{gcs_scope.data_access}]" for base_scope in self.base_scopes
        ]

        submission_scope = self.gconfig.get_transfer_submission_scope()
        if submission_scope:
            requested_scopes.append(f"{submission_scope}[{gcs_scope.data_access}]")

        return " ".join(requested_scopes)

    def get_login_url(self):
        login_url = self.reverse_url("login")
        params = urllib.parse.urlencode(
            {"requested_scopes": self.get_requested_scopes()}
        )
        return f"{login_url}?{params}"


class GlobusSDKWrapper(BaseAPIHandler):

    globus_sdk_method = None
    mandatory_args = []
    optional_args = {}

    def get_requested_scopes(self):
        return " ".join(self.gconfig.get_scopes())

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
            if gapie.http_status in [401, 403]:
                response["login_url"] = self.get_login_url()
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


class EndpointAutoactivate(GCSAuthMixin, POSTMethodTransferAPIEndpoint):
    """An API Endpoint doing a Globus LS"""

    globus_sdk_method = "endpoint_autoactivate"
    mandatory_args = ["endpoint_id"]
    optional_args = {}


class SubmitTransfer(GCSAuthMixin, BaseAPIHandler):
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
                response["login_url"] = self.get_login_url()
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
    optional_args = {"path": None}


class EndpointSearch(GCSAuthMixin, GetMethodTransferAPIEndpoint):
    """An API Endpoint for searching for collections"""

    globus_sdk_method = "endpoint_search"
    mandatory_args = []
    optional_args = {
        "filter_fulltext": None,
        "filter_scope": None,
        "filter_owner_id": None,
        "filter_host_endpoint": None,
        "filter_non_functional": None,
        "limit": None,
        "offset": None,
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
