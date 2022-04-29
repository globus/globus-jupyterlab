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
