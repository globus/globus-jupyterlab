import time
import re

MOCK_TOKENS = {
    "transfer.api.globus.org": {
        "access_token": "mock_user_access_token",
        # Simulate brand new fresh tokens that expire in 48 hours
        "expires_at_seconds": int(time.time()) + 60 * 60 * 48,
        "refresh_token": None,
        "resource_server": "transfer.api.globus.org",
        "scope": "urn:globus:auth:scope:transfer.api.globus.org:all",
        "token_type": "Bearer",
    }
}


class SDKResponse:
    def __init__(self, data=None):
        self._data = data or dict()

    @property
    def data(self):
        return self._data


class MockGlobusAPIError(Exception):
    def __init__(self, message, http_status=400, code="error"):
        self.http_status = http_status
        self.code = code
        self.message = message


GRIDFTP_HA_NOT_FROM_ALLOWED_DOMAIN = r"""Error validating login to endpoint 'Globus Staff GCSv5.4 Demo POSIX HA (eed63c24-36cb-4f29-a47f-91d94a65fef8)', Error (login)
Endpoint: Globus Staff GCSv5.4 Demo POSIX HA (eed63c24-36cb-4f29-a47f-91d94a65fef8)
Server: m-8c970f.fa5e.bd7c.data.globus.org:443
Message: Login Failed
---
Details: 530-Login incorrect. : GlobusError: v=1 c=LOGIN_DENIED\r\n530-GridFTP-Message: None of your identities are from domains allowed by resource policies\r\n530-GridFTP-JSON-Result: {"DATA_TYPE": "result#1.0.0", "code": "permission_denied", "detail": {"DATA_TYPE": "not_from_allowed_domain#1.0.0", "allowed_domains": ["globus.org"]}, "has_next_page": false, "http_response_code": 403, "message": "None of your identities are from domains allowed by resource policies"}\r\n530 End.\r\n"""

GRIDFTP_S3_CREDENTIALS_REQUIRED_MESSAGE = r"""Error validating login to endpoint 'Globus Staff GCSv5.4 Demo S3 (9bdac9c3-b409-4ca9-91df-8c29f294f1f9)', Error (login)
Endpoint: Globus Staff GCSv5.4 Demo S3 (9bdac9c3-b409-4ca9-91df-8c29f294f1f9)
Server: m-b3abc7.fa5e.bd7c.data.globus.org:443
Message: Login Failed
---
Details: 530-Login incorrect. : GlobusError: v=1 c=LOGIN_DENIED\r\n530-GridFTP-Message: Your credential requires some initial setup.\r\n530-GridFTP-JSON-Result: {"DATA_TYPE": "result#1.0.0", "code": "invalid_credential", "detail": {"DATA_TYPE": "invalid_credential#1.0.0", "user_credential_id": "249248d1-df8e-5c27-8d43-7b35a8924004"}, "has_next_page": false, "http_response_code": 403, "message": "Your credential requires some initial setup."}\r\n530 End.\r\n
"""

GRIDFTP_UNEXPECTED_MESSAGE = r"""Error validating login to endpoint 'Globus Staff Interdimensional (9xdac9c3-b409-4ca9-91df-8c29f294f1f9)', Error (login)
Endpoint: Globus Staff Interdimensional (9xdac9c3-b409-4ca9-91df-8c29f294f1f9)
Server: m-bxabc7.fa5e.bd7c.data.globus.org:443
Message: Login Failed
---
Details: 530-Login incorrect. : GlobusError: v=1 c=LOGIN_DENIED\r\n530-GridFTP-Message: Something Horrible Happened.\r\n530-GridFTP-JSON-Result: {"DATA_TYPE": "result#1.0.0", "code": "invalid_credential", "detail": {"DATA_TYPE": "does_not_exist#1.0.0", "user_credential_id": "249248d1-df8e-5c27-8d43-7b35a8924004"}, "has_next_page": false, "http_response_code": 403, "message": "The collection appears to have been blown up by a giant moon laser. Before attempting to fix this problem, you should probably find somewhere to hide. Like right now. Seriously."}\r\n530 End.\r\n
"""

for message in [
    GRIDFTP_HA_NOT_FROM_ALLOWED_DOMAIN,
    GRIDFTP_S3_CREDENTIALS_REQUIRED_MESSAGE,
    GRIDFTP_UNEXPECTED_MESSAGE,
]:
    assert re.search(r"530-GridFTP-JSON-Result: (.+)\\r\\n530 End", message), f'Mock messages not setup correctly! {message}'
