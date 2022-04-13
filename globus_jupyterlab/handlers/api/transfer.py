
import json
import urllib
import tornado
import globus_sdk
import pydantic
from globus_jupyterlab.handlers.base import BaseAPIHandler
from globus_jupyterlab.models import TransferModel


class GCSAuthMixin(BaseAPIHandler):
    """Mixin for handling 403 responses from querying a Globus Connect Server which
    requries the data_access scope. This mixin will introspect the query params for
    the collection using `gcs_query_param`. This value needs to match the expected
    gcs query param or the request will fail.

    For 403 responses, responses will include a login urls with the extended scopes
    for the data_access scope, for each `base_scope` defined below (by default it
    is only transfer) Additionally, if a custom transfer submission scope is used,
    that will also be automatically requested."""

    gcs_query_param = 'endpoint'
    base_scopes = [globus_sdk.scopes.TransferScopes.all]

    def get_requested_scopes(self):
        collection = self.get_query_argument(self.gcs_query_param)
        gcs_scope = globus_sdk.scopes.GCSCollectionScopeBuilder(collection)
        requested_scopes = [f'{base_scope}[{gcs_scope.data_access}]' for base_scope in self.base_scopes]

        submission_scope = self.gconfig.get_transfer_submission_scope()
        if submission_scope:
            requested_scopes.append(f'{submission_scope}[{gcs_scope.data_access}]')

        return ' '.join(requested_scopes)


class GetMethodTransferAPIEndpoint(BaseAPIHandler):

    globus_sdk_method = None
    mandatory_args = []
    optional_args = {}

    def get_requested_scopes(self):
        return ' '.join(self.gconfig.get_scopes())

    def get(self):
        response = dict()
        if self.login_manager.is_logged_in() is not True:
            self.set_status(401)
            return self.finish(json.dumps({'error': 'The user is not logged in'}))
        try:
            authorizer = self.login_manager.get_authorizer('transfer.api.globus.org')
            tc = globus_sdk.TransferClient(authorizer=authorizer)
            method = getattr(tc, self.globus_sdk_method)
            args, kwargs = self.get_args()
            response = method(*args, **kwargs)
            return self.finish(json.dumps(response.data))
        except globus_sdk.GlobusAPIError as gapie:
            self.set_status(gapie.http_status)
            response = {'error': gapie.code, 'details': gapie.message}
            if gapie.http_status in [401, 403]:
                login_url = self.reverse_url('login')
                params = urllib.parse.urlencode({'requested_scopes': self.get_requested_scopes()})
                response['login_url'] = f'{login_url}?{params}'
            return self.finish(json.dumps(response))

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


class OperationLS(GCSAuthMixin, GetMethodTransferAPIEndpoint):
    """An API Endpoint doing a Globus LS"""
    globus_sdk_method = 'operation_ls'
    mandatory_args = ['endpoint']
    optional_args = {
        'path': None
    }


class EndpointSearch(GCSAuthMixin, GetMethodTransferAPIEndpoint):
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


class EndpointDetail(GCSAuthMixin, GetMethodTransferAPIEndpoint):
    globus_sdk_method = 'get_endpoint'
    mandatory_args = ['endpoint']
    optional_args = {}


default_handlers = [
    ('/submit_transfer', SubmitTransfer, dict(), 'submit_transfer'),
    ('/operation_ls', OperationLS, dict(), 'operation_ls'),
    ('/endpoint_search', EndpointSearch, dict(), 'endpoint_search'),
    ('/endpoint_detail', EndpointDetail, dict(), 'endpoint_detail'),
]
