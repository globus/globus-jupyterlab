import time
import re

now_seconds = int(time.time())
two_days_from_now_seconds = now_seconds * 60 * 60 * 48

MOCK_TOKENS = {
    "transfer.api.globus.org": {
        "access_token": "mock_user_access_token",
        "expires_at_seconds": two_days_from_now_seconds,
        "refresh_token": None,
        "resource_server": "transfer.api.globus.org",
        "scope": "urn:globus:auth:scope:transfer.api.globus.org:all",
        "token_type": "Bearer",
    },
    "auth.globus.org": {
        "access_token": "auth_access_token",
        "expires_at_seconds": two_days_from_now_seconds,
        "refresh_token": None,
        "resource_server": "auth.globus.org",
        "scope": "openid profile",
        "token_type": "Bearer",
    },
}

MOCK_IDENTITIES = {
    "sub": "e5446c8f-bf6c-4db1-9e3c-b0987b385172",
    "organization": "Globus",
    "name": "Owl Lady",
    "preferred_username": "theowllady@globusid.org",
    "identity_provider": "228a7af8-16a2-486c-b212-d8c7860d16e2",
    "identity_provider_display_name": "Globus ID",
    "last_authentication": 1654732330,
    "identity_set": [
        {
            "sub": "e5446c8f-bf6c-4db1-9e3c-b0987b385172",
            "organization": "Globus",
            "name": "Owl Lady",
            "username": "theowllady@globusid.org",
            "identity_provider": "228a7af8-16a2-486c-b212-d8c7860d16e2",
            "identity_provider_display_name": "Globus ID",
            "last_authentication": now_seconds,
        },
        {
            "sub": "7d4657a1-0422-409a-a0ee-077f4a6a99a1",
            "name": "Owl Lady",
            "username": "theowllady@globus.org",
            "identity_provider": "04b5377c-3b1a-4e9d-b84c-bdeaa6c2fc1f",
            "identity_provider_display_name": "Globus Staff",
            "last_authentication": now_seconds,
        },
    ],
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
    assert re.search(
        r"530-GridFTP-JSON-Result: (.+)\\r\\n530 End", message
    ), f"Mock messages not setup correctly! {message}"
