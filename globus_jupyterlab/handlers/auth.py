from logging import exception
import urllib
import globus_sdk
from typing import List
from globus_sdk.scopes import TransferScopes
from globus_jupyterlab.exc import DataAccessScopesRequired
from globus_jupyterlab.handlers.base import BaseAPIHandler
from globus_jupyterlab.handlers import exception_handlers


class AutoAuthURLMixin(BaseAPIHandler):
    endpoint_or_collection_parameter = None
    login_checks = [
        exception_handlers.LoginRequired,
    ]

    def get_exception_info(self, exception: globus_sdk.GlobusAPIError) -> bool:
        info = {
            "error": exception.code,
            "details": exception.message,
        }
        exc_handler = self.get_login_exception_handler(exception)
        if exc_handler is not None:
            info.update(exc_handler.metadata)
            info["login_url"] = self.get_globus_login_url(exc_handler)
        else:
            info.update(
                {
                    "login_required": False,
                    "requires_user_intervention": False,
                }
            )
        return info

    def get_endpoint_or_collection(self) -> str:
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
            if exception_handler is None:
                return self.gconfig.get_transfer_scopes
            return exception_handler.get_extended_scopes(
                self.gconfig.get_transfer_scopes()
            )
        except DataAccessScopesRequired:
            new_scopes = []
            dependent_scope = globus_sdk.scopes.GCSCollectionScopeBuilder(
                self.get_endpoint_or_collection()
            )
            transfer_with_data_access = self.login_manager.apply_dependent_scopes(
                self.gconfig.transfer_scope, [dependent_scope.data_access]
            )
            new_scopes.append(transfer_with_data_access)

            custom_t_scope = self.gconfig.get_transfer_submission_scope()
            if custom_t_scope:
                custom_w_dep = self.login_manager.apply_dependent_scopes(
                    custom_t_scope, [transfer_with_data_access]
                )
                new_scopes.append(custom_w_dep)

            return new_scopes

    def get_required_identities(self, domains: List[str]) -> List[str]:
        authorizer = self.login_manager.get_authorizer("auth.globus.org")
        auth_client = globus_sdk.AuthClient(
            client_id=self.login_manager.client_id, authorizer=authorizer
        )
        response = auth_client.oauth2_userinfo()
        return [
            ident["sub"]
            for ident in response.data["identity_set"]
            if any([domain in ident["username"] for domain in domains])
        ]

    def get_globus_login_url(
        self, exception_handler: exception_handlers.AuthExceptionHandler
    ) -> str:

        params = dict(
            requested_scopes=" ".join(self.get_requested_scopes(exception_handler)),
            prompt="login",
        )
        domains = exception_handler.get_required_session_domains()
        if domains:
            params["session_required_identities"] = ",".join(
                self.get_required_identities(domains)
            )
            params[
                "session_message"
            ] = "The collection you selected requires a fresh login"

        full_login_url = urllib.parse.urlunparse(
            (
                self.request.protocol,
                self.request.host,
                self.reverse_url("login"),
                "",
                urllib.parse.urlencode(params),
                "",
            )
        )
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

    def get_globus_login_url(
        self, exception_handler: exception_handlers.AuthExceptionHandler
    ) -> str:
        if exception_handler and exception_handler.requires_user_intervention:
            return f"https://app.globus.org/file-manager?origin_id={self.get_endpoint_or_collection()}"
        return super().get_globus_login_url(exception_handler)
