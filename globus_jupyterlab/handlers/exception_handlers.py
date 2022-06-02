import abc
import json
import re
from typing import List
import globus_sdk
from globus_jupyterlab.exc import DataAccessScopesRequired, LoginException


class AuthExceptionHandler(abc.ABC):

    requires_session_identities = False
    requires_endpoint = False
    requires_transfer_scopes = True

    def __init__(self, exception: globus_sdk.GlobusAPIError):
        self.exception = exception
        self.endpoint = None
        self.available_session_identities = None
        self.requires_transfer_scopes = None

    @abc.abstractmethod
    def check(self) -> bool:
        pass

    def get_custom_login_url(self) -> str:
        return None

    def get_extended_scopes(self, transfer_scopes: List) -> list:
        return transfer_scopes

    def get_required_session_domains(self) -> list:
        return None


class GCSAuthExceptionHandler(AuthExceptionHandler):
    def __init__(self, exception: globus_sdk.GlobusAPIError):
        super().__init__(exception)
        self.gridftp_response = self.parse_gridftp_json_response(self.exception.message)

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


class LoginRequired(AuthExceptionHandler):
    def check(self):
        return self.exception.http_status == 401


class GCSv4Endpoint(GCSAuthExceptionHandler):

    requires_endpoint = True

    def check(self) -> bool:
        return (
            self.exception.http_status == 400
            and self.exception.code == "ClientError.ActivationRequired"
        )

    def get_custom_login_url(self) -> str:
        return f"https://app.globus.org/file-manager?origin_id={self.endpoint}"


class GCSv54HighAssurance(GCSAuthExceptionHandler):
    def check(self) -> bool:
        return (
            self.exception.http_status == 502
            and self.gridftp_response
            and self.gridftp_response.get("detail", {}).get("DATA_TYPE")
            == "not_from_allowed_domain#1.0.0"
        )

    def get_required_session_domains(self):
        domains = self.gridftp_response["detail"]["allowed_domains"]
        return domains


class GCSv54S3Credentials(GCSAuthExceptionHandler):
    requires_endpoint = True

    def check(self) -> bool:
        return (
            self.exception.http_status == 502
            and self.gridftp_response
            and self.gridftp_response.get("detail", {}).get("DATA_TYPE")
            == "invalid_credential#1.0.0"
        )

    def get_custom_login_url(self) -> str:
        return f"https://app.globus.org/file-manager?origin_id={self.endpoint}"


class GCSUnexpectedGridFTPError(GCSAuthExceptionHandler):
    requires_endpoint = True

    def check(self) -> bool:

        return bool(self.exception.http_status == 502 and self.gridftp_response)

    def get_custom_login_url(self) -> str:
        return f"https://app.globus.org/file-manager?origin_id={self.endpoint}"


class GCSv54DataAccessConsent(GCSAuthExceptionHandler):
    def check(self) -> bool:
        """
        Collection is a GCS v5.4 mapped collection and requires a data_access scope
        """
        return (
            self.exception.http_status == 403
            and self.exception.code == "ConsentRequired"
        )

    def get_extended_scopes(self, transfer_scopes):
        raise DataAccessScopesRequired(f"data_access scope required!")
