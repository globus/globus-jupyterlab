import tornado

from globus_jupyterlab.handlers.base import BaseAPIHandler, RedirectWebHandler


class Login(BaseAPIHandler):

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        """
        Redirect to Globus Auth for the first 'authorization' hop.
        """
        # self.finish()
        pass


class AuthCallback(RedirectWebHandler):

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        """
        Revoke all local Gloubs tokens
        """
        pass


class Logout(BaseAPIHandler):

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
