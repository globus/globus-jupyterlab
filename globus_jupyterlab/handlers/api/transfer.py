
import json
import tornado
import globus_sdk
import pydantic
from globus_jupyterlab.handlers.base import BaseAPIHandler
from globus_jupyterlab.models import TransferModel


class GetMethodTransferAPIEndpoint(BaseAPIHandler):

    globus_sdk_method = None
    mandatory_args = []
    optional_args = {}

    def get(self):
        response = dict()
        if self.login_manager.is_logged_in() is not True:
            self.set_status(401)
            return self.finish(json.dumps({'error': 'The user is not logged in'}))
        try:
            authorizer = self.login_manager.get_authorizer(
                'transfer.api.globus.org')
            tc = globus_sdk.TransferClient(authorizer=authorizer)
            method = getattr(tc, self.globus_sdk_method)
            args, kwargs = self.get_args()
            response = method(*args, **kwargs)
            return self.finish(json.dumps(response.data))
        except globus_sdk.GlobusAPIError as gapie:
            self.set_status(gapie.http_status)
            return self.finish(json.dumps({'error': gapie.code, 'details': gapie.message}))

    def get_args(self):
        args = [self.get_query_argument(arg) for arg in self.mandatory_args]
        kwargs = {arg: self.get_query_argument(arg, default)
                  for arg, default in self.optional_args.items()}
        return args, kwargs


class SubmitTransfer(BaseAPIHandler):
    """An API Endpoint for submitting Globus Transfers."""

    @tornado.web.authenticated
    def post(self):
        """
        Attempt to submit a transfer with tokens previously loaded by a user.
        """
        response = dict()
        if self.login_manager.is_logged_in() is not True:
            self.set_status(401)
            return self.finish(json.dumps({'error': 'The user is not logged in'}))
        try:
            post_data = json.loads(self.request.body)
            tm = TransferModel(**post_data)

            authorizer = self.login_manager.get_authorizer(
                'transfer.api.globus.org')
            tc = globus_sdk.TransferClient(authorizer=authorizer)

            td = globus_sdk.TransferData(
                tc, tm.source_endpoint, tm.destination_endpoint)
            for transfer_item in tm.transfer_items:
                td.add_item(transfer_item.source_path,
                            transfer_item.destination_path,
                            recursive=transfer_item.recursive)
            response = tc.submit_transfer(td)
            return self.finish(json.dumps(response.data))
        except pydantic.ValidationError as ve:
            self.set_status(400)
            return self.finish(json.dumps({'error': 'Invalid Input', 'details': ve.json()}))


class OperationLS(GetMethodTransferAPIEndpoint):
    """An API Endpoint doing a Globus LS"""
    globus_sdk_method = 'operation_ls'
    mandatory_args = ['endpoint']
    optional_args = {
        'path': None
    }


class EndpointSearch(GetMethodTransferAPIEndpoint):
    """An API Endpoint for searching for collections"""
    globus_sdk_method = 'endpoint_search'
    mandatory_args = []
    optional_args = {
        'filter_fulltext': None,
        'filter_scope': None,
        'filter_owner_id': None,
        'filter_host_endpoint': None,
        'filter_non_functional': None,
        'limit': None,
        'offset': None,
    }


default_handlers = [
    ('/submit_transfer', SubmitTransfer, dict(), 'submit_transfer'),
    ('/operation_ls', OperationLS, dict(), 'operation_ls'),
    ('/endpoint_search', EndpointSearch, dict(), 'endpoint_search'),
]
