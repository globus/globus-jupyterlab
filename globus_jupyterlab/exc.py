class GlobusJupyterlabException(Exception):
    """A generic exception that happened within the Globus JupyterLab extension"""

    pass


class TransferSubmission(GlobusJupyterlabException):
    """Something happened when attempting to submit a transfer"""

    pass


class LoginException(GlobusJupyterlabException):
    """There was a problem with the login process"""

    pass


class TokenStorageError(GlobusJupyterlabException):
    """A problem loading user Globus tokens"""

    pass
