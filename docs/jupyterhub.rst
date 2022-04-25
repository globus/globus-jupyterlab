JupyterHub
==========

For the most part, running JupyterLab in a hub environment is the same as running
locally on a workstation. However, GCS Collections cannot automatically be determined
like they can on Globus Connect Personal. Custom collections will need to be speficied
manually.

.. code-block:: bash

   export GLOBUS_COLLECTION='MyCollectionUUID'


Customized Transfer Submissions
-------------------------------

By default, JupyterLab will talk directly to Globus Transfer for submitting transfers.
This behavior is customizable if desired, such that JupyterLab can submit to a third-party
Globus Resource Server instead. This is useful when work needs to be done before or after
a transfer such as setting ACLs. 

.. code-block:: bash

   export GLOBUS_TRANSFER_SUBMISSION_URL='https://myservice/submit-transfer'
   export GLOBUS_TRANSFER_SUBMISSION_SCOPE='my_custom_globus_scope'
   export GLOBUS_TRANSFER_SUBMISSION_URL_USES_HUB_AUTH=true

With these settings configured, Jupyterlab will behave slightly differently during runtime.
The configured scope above will be requested on first login in addition to the original transfer
scope. When a user requests a transfer, the custom ``URL`` above will be used instead of transfer,
with the following request:

.. code-block:: javascript

    {
        "transfer": {
            "source_endpoint": "ddb59aef-6d04-11e5-ba46-22000b92c6ec",
            "destination_endpoint": "ddb59af0-6d04-11e5-ba46-22000b92c6ec",
            "DATA": [
                {
                    "source_path": "/share/godata/file1.txt",
                    "destination": "~/",
                    "recursive": false
                },
                {
                    "source_path": "/foo/bar",
                    "destination": "~/bar",
                    "recursive": true
                }
            ]
        }
    }

The custom request is expected to return the following response:

.. code-block::

    {
        "task_id": “abcdeaef-6d04-11e5-ba46-22000b92c6ec"
    }

The task ID returned by the service will be used to monitor the task in Globus.
