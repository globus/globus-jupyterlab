import json
import re
import urllib
import globus_sdk
from typing import List
from globus_jupyterlab.exc import LoginException
from globus_jupyterlab.handlers.base import BaseAPIHandler


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
