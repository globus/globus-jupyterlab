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
        Revoke all local Gloubs tokens
        """
        pass


default_handlers = [('/login', Login, dict(), 'login'),
                    ('/logout', Logout, dict(), 'logout'),
                    ('/oauth_callback', AuthCallback, dict(), 'redirect_uri')]
