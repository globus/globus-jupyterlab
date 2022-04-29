import json
import tornado
from globus_jupyterlab.handlers.base import BaseAPIHandler


class Config(BaseAPIHandler):
    """API Endpoint for fetching information about how the Juptyerlab Backend is configured.
    Configuration can be customized through the hub, such as by setting the Globus Collection
    where the hub prefers its transfers, or alternatively by the user's local installation if
    they have GCP installed."""

    @tornado.web.authenticated
    def get(self, *args, **kwargs):

        copy_required = (
            self.gconfig.get_redirect_uri()
            == self.gconfig.globus_auth_code_redirect_url
        )
        data = {
            # TODO: Make these configurable
            "collection_id": self.gconfig.get_collection_id(),
            "collection_base_path": self.gconfig.get_collection_path(),
            "is_gcp": self.gconfig.is_gcp(),
            "is_hub": self.gconfig.is_hub(),
            "is_manual_copy_code_required": copy_required,
            "is_logged_in": self.login_manager.is_logged_in(),
            "collection_id_owner": self.gconfig.get_collection_id_owner(),
        }
        self.finish(json.dumps(data))


default_handlers = [("/config", Config, {}, "config")]
