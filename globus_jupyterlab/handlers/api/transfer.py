
import json
import tornado
import globus_sdk
import pydantic
from globus_jupyterlab.handlers.base import BaseAPIHandler
from globus_jupyterlab.models import TransferModel


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


default_handlers = [('/submit_transfer', SubmitTransfer, dict(), 'submit_transfer')]
