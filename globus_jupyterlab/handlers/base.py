from notebook.base.handlers import APIHandler
from globus_jupyterlab.globus_config import GlobusConfig
from globus_jupyterlab.login_manager import LoginManager

globus_config = GlobusConfig()


class BaseAPIHandler(APIHandler):
    gconfig = globus_config
    login_manager = LoginManager(globus_config.get_client_id())


class RedirectWebHandler(BaseAPIHandler):
    """Redirect Web Handlers are intended for redirecting outside of the Jupyterlab
    app. This can be used for both the OAuth web flow, or alternativly helper pages."""

    def set_default_headers(self, *args, **kwargs):
        """This is needed for redirect back to JupyterLab from an outside source.
        Typically, this is shady and will cause a security warning from Jupyter Server, but
        for intentional usage we need to tell Jupyterlab to ignore the source from a third
        party server."""
        # We should look into this to see if we can get more specific, such as by setting
        # auth.globus.org, or app.globus.org.
        self.set_header("Content-Security-Policy", "*")
