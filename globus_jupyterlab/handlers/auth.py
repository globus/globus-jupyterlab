import urllib
import globus_sdk
from globus_jupyterlab.exc import DataAccessScopesRequired
from globus_jupyterlab.handlers.base import BaseAPIHandler
from globus_jupyterlab.handlers import exception_handlers


class AutoAuthURLMixin(BaseAPIHandler):
    endpoint_or_collection_parameter = None
    login_checks = [
        exception_handlers.LoginRequired,
    ]

    def get_endpoint_or_collection(self):
        """
        Used internally by exception handlers when an endpoint or collection is needed
        to determine the next course of action. For example, a gcs v4 endpoint needs activation.

        MUST be implemented by API Handlers which may have auth related errors on specific endpoints.
        """
        col = getattr(self, "endpoint_or_collection_parameter", None)
        if col is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} did not reference an endpoint or collection "
                "parameter for transfer operations. It should define `endpoint_or_collection_parameter`."
            )
        return self.get_argument(col)

    def is_login_required(self, exception: globus_sdk.GlobusAPIError) -> bool:
        """
        Check if the exception requries login. For normal calls to services, this just
        means a 401, but there are a slew of possible login cases for GCS.
        """
        return bool(self.get_login_exception_handler(exception))

    def get_login_exception_handler(
        self, exception: globus_sdk.GlobusAPIError
    ) -> exception_handlers.AuthExceptionHandler:
        for cls in self.login_checks:
            instance = cls(exception)
            check_value = instance.check()
            self.log.debug(f"Checking {cls.__name__}: {check_value}")
            if check_value is True:
                return instance

    def get_requested_scopes(
        self, exception_handler: exception_handlers.AuthExceptionHandler
    ) -> list:
        try:
            return exception_handler.get_extended_scopes(self.gconfig.get_scopes())
        except DataAccessScopesRequired:
            dependent_scope = globus_sdk.scopes.GCSCollectionScopeBuilder(
                self.get_endpoint_or_collection()
            )
            return [
                self.login_manager.apply_dependent_scopes(
                    base, [dependent_scope.data_access]
                )
                for base in self.gconfig.get_scopes()
            ]

    def get_globus_login_url(self, exception: globus_sdk.GlobusAPIError) -> str:
        exception_handler = self.get_login_exception_handler(exception)
        custom_login_url = exception_handler.get_custom_login_url()
        if custom_login_url:
            return custom_login_url
        login_url = self.reverse_url("login")

        params = dict(
            requested_scopes=" ".join(self.get_requested_scopes(exception_handler)),
        )
        domains = exception_handler.get_required_session_domains()
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

    login_checks = [
        exception_handlers.LoginRequired,
        exception_handlers.GCSv4Endpoint,
        exception_handlers.GCSv54HighAssurance,
        exception_handlers.GCSv54S3Credentials,
        exception_handlers.GCSv54DataAccessConsent,
        # Note! This should always be last, after all other GRIDFTP error types!
        exception_handlers.GCSUnexpectedGridFTPError,
    ]

    def get_login_exception_handler(
        self, exception: globus_sdk.GlobusAPIError
    ) -> exception_handlers.AuthExceptionHandler:
        handler = super().get_login_exception_handler(exception)
        if handler and handler.requires_endpoint:
            handler.endpoint = self.get_endpoint_or_collection()
        return handler
