JupyterHub
==========

For the most part, running JupyterLab in a Hub environment is the same as running JupyterLab
locally on a workstation. 

Users can transfer to or from any accessible Globus endpoint or collection. As a convenience, 
Globus JupyterLab will automatically detect a local, running Globus Connect Personal endpoint. 
Globus Connect Personal may be downloaded from the Globus web application. https://app.globus.org/file-manager/gcp

Globus Connect Server collections cannot be determined automatically.  These collections will need to be speficied
manually.

.. code-block:: bash

   export GLOBUS_COLLECTION_ID='MyCollectionUUID'


Customized Transfer Submissions
-------------------------------

By default, JupyterLab submits transfer requests directly to Globus Transfer.
This behavior is customizable such that JupyterLab submits to a third-party
Globus Resource Server instead. This is useful when a third-party app needs to
submit the transfer request to Globus Transfer. 

.. code-block:: bash

   export GLOBUS_TRANSFER_SUBMISSION_URL='https://myservice/submit-transfer'
   export GLOBUS_TRANSFER_SUBMISSION_SCOPE='my_custom_globus_scope'
   export GLOBUS_TRANSFER_SUBMISSION_IS_HUB_SERVICE=true

With these settings configured, Jupyterlab will request the configured scope above on first login, in addition to the original transfer
scope. When a user requests a transfer, the request will be submitted to the custom ``URL`` above instead of to Globus Transfer,
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
