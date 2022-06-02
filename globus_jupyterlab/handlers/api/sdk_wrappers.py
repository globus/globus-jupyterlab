import json
import globus_sdk
from globus_jupyterlab.exc import LoginException
from globus_jupyterlab.handlers.auth import AutoAuthURLMixin


class GlobusSDKWrapper(AutoAuthURLMixin):
    """
    Wrapper for the Globus SDK. This is a base class for wrapping the globus-sdk
    with anothher API layer for the Globus Jupyterlab frontend. The front-end can
    then make requests to the JupyterLab server extension, using this layer to
    translate calls into various Globus Service calls.
    """

    globus_sdk_method = None
    mandatory_args = []
    optional_args = {}

    def get_globus_sdk_args(self):
        return [], {}

    def transfer_client_call(self):
        authorizer = self.login_manager.get_authorizer("transfer.api.globus.org")
        tc = globus_sdk.TransferClient(authorizer=authorizer)
        method = getattr(tc, self.globus_sdk_method)
        args, kwargs = self.get_globus_sdk_args()
        return method(*args, **kwargs).data

    def sdk_wrapper_call(self):
        response = dict()
        if self.login_manager.is_logged_in() is not True:
            self.set_status(401)
            return self.finish(json.dumps({"error": "The user is not logged in"}))
        try:
            return self.finish(json.dumps(self.transfer_client_call()))
        except globus_sdk.GlobusAPIError as gapie:
            self.set_status(gapie.http_status)
            response = {
                "error": gapie.code,
                "details": gapie.message,
                "login_required": self.is_login_required(gapie),
            }
            self.log.debug(
                f'Globus SDK Error encountered, Login Required to fix above error? {response["login_required"]}',
                exc_info=True,
            )
            if response["login_required"] is True:
                try:
                    self.set_status(401)
                    response["login_url"] = self.get_globus_login_url(gapie)
                except LoginException as le:
                    self.log.error("Failed to generate login URL", exc_info=True)
                    response["error"] = le.__class__.__name__
                    response["details"] = str(le)
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
