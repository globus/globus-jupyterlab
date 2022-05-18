import time

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
