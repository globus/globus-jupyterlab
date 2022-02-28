import tornado

from notebook.base.handlers import APIHandler
from globus_jupyterlab.handlers.base import RedirectWebHandler


class Login(APIHandler):

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        """
        Redirect to Globus Auth for the first 'authorization' hop.
        """
        # self.finish()
        pass


class Logout(APIHandler):

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        """
        Revoke all local Gloubs tokens
        """
        pass


class AuthCallback(RedirectWebHandler):

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        """
        Accept a redirect from Globus Auth, and process the 'auth_code' in the query params.
        """
        # self.finish()
        pass


default_handlers = [('/login', Login),
                    ('/logout', Logout),
                    ('/oauth_callback', AuthCallback)]
