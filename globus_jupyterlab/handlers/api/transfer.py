import json
import pathlib
import globus_sdk
import pydantic
import requests
from globus_jupyterlab.exc import TransferSubmission
from globus_jupyterlab.models import TransferModel
from globus_jupyterlab.handlers.auth import GCSAuthMixin
from globus_jupyterlab.handlers.api.sdk_wrappers import (
    GetMethodTransferAPIEndpoint,
    POSTMethodTransferAPIEndpoint,
)


class EndpointAutoactivate(POSTMethodTransferAPIEndpoint):
    """An API Endpoint doing a Globus LS"""

    globus_sdk_method = "endpoint_autoactivate"
    mandatory_args = ["endpoint_id"]
    optional_args = {}
    endpoint_or_collection_parameter = "endpoint_id"


class SubmitTransfer(GCSAuthMixin, POSTMethodTransferAPIEndpoint):
    """An API Endpoint for submitting Globus Transfers."""

    globus_sdk_method = "submit_transfer"
    mandatory_args = []
    optional_args = {}

    def translate_base_paths(self, path: str) -> TransferModel:
        """
        Take the path that JupyterLab generated and translate it into a "Globus" collection acessible
        path. This is typically needed if the mount path on the collection causes a 'mismatch' in paths
        between how JupyterLab sees files and the Collection sees files.
        """
        user_transfer_path = pathlib.Path(path)
        host_collection_basepath = pathlib.Path(
            self.gconfig.get_host_collection_basepath()
        )
        host_posix_basepath = self.gconfig.get_host_posix_basepath()

        if not user_transfer_path.exists():
            self.log.warning(
                f"User specified path {user_transfer_path} does not exist!"
            )

        if host_posix_basepath:
            try:
                user_transfer_path = user_transfer_path.relative_to(host_posix_basepath)
            except ValueError:
                raise TransferSubmission(
                    f"Path {user_transfer_path} is not in the subpath of {host_posix_basepath}, and is inaccessible via the configured Globus Collection. Consider moving {user_transfer_path} into {host_posix_basepath} first."
                ) from None

        if host_collection_basepath:
            user_transfer_path = host_collection_basepath / user_transfer_path

        return str(user_transfer_path)

    def translate_transfer_submission(
        self, transfer_model: TransferModel
    ) -> TransferModel:
        col_id = self.gconfig.get_collection_id()
        for transfer_items in transfer_model.DATA:
            if transfer_model.source_endpoint == col_id:
                new_path = self.translate_base_paths(transfer_items.source_path)
                self.log.debug(
                    f"Translating source path {transfer_items.source_path} --> {new_path}"
                )
                transfer_items.source_path = new_path

            elif transfer_model.destination_endpoint == col_id:
                new_path = self.translate_base_paths(transfer_items.destination_path)
                self.log.debug(
                    f"Translating destination path {transfer_items.destination_path} --> {new_path}"
                )
                transfer_items.destination_path = new_path
            else:
                raise ValueError(
                    f"Non-local collection used in transfer, expected '{col_id}' in transfer. The following transfer document is invalid: {transfer_model.json()}"
                )

    def transfer_client_call(self):
        """Transfer submission is a bit more complex than the other wrapped calls. For one, it validates
        a complex POST document through pydantic instead of taking simple args. Second, the call into the
        Transfer Client requires a couple helper classes to complete, including both globus_sdk.TransferClient
        and globus_sdk.TransferModel. Third, the globus_sdk may not be used in the case that a separate
        service is handling the actual transfer, in which case the document needs to be forwarded instead.

        Auth errors are the only unchanged mechanism. If the remote endpoint isn't active or requires
        re-auth, the procedure is the same as other operation methods.
        """
        try:
            post_data = json.loads(self.request.body)
            self.log.debug("Checking transfer document")
            tm = TransferModel(**post_data)
            self.translate_transfer_submission(tm)
            if self.gconfig.get_transfer_submission_url():
                response = self.submit_custom_transfer(tm)
            else:
                response = self.submit_normal_transfer(tm)
            self.log.info("User transfer submission succeeded.")
            return response
        except pydantic.ValidationError as ve:
            self.set_status(400)
            self.log.debug("Transfer doc failed validation", exc_info=True)
            return {"error": "Invalid Input", "details": ve.json()}
        except TransferSubmission as ts:
            self.set_status(400)
            self.log.info("User error for attempted Globus Transfer", exc_info=True)
            return {"error": "Invalid Input", "details": str(ts)}

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
            tc,
            transfer_data.source_endpoint,
            transfer_data.destination_endpoint,
            label=transfer_data.label,
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
    endpoint_or_collection_parameter = "endpoint"


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
    endpoint_or_collection_parameter = "endpoint"


default_handlers = [
    ("/submit_transfer", SubmitTransfer, dict(), "submit_transfer"),
    ("/operation_ls", OperationLS, dict(), "operation_ls"),
    ("/endpoint_search", EndpointSearch, dict(), "endpoint_search"),
    ("/endpoint_detail", EndpointDetail, dict(), "endpoint_detail"),
    ("/endpoint_autoactivate", EndpointAutoactivate, dict(), "endpoint_autoactivate"),
]
