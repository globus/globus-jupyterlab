Hub-Managed Service Transfers
=============================

By default, JupyterLab submits transfer requests directly to Globus Transfer.
This behavior is customizable such that JupyterLab submits to a third-party
Globus Resource Server instead. This is useful when a third-party app needs to
submit the transfer request to Globus Transfer.

.. code-block:: bash

   export GLOBUS_TRANSFER_SUBMISSION_URL='https://myservice.edu/service/acls-service'
   export GLOBUS_TRANSFER_SUBMISSION_SCOPE='my_custom_globus_scope'
   export GLOBUS_TRANSFER_SUBMISSION_IS_HUB_SERVICE=true

With these settings configured, Jupyterlab will request the configured scope above on first login, in addition to the original transfer
scope. When a user requests a transfer, the request will be submitted to the custom ``URL`` above instead of to Globus Transfer,
with the following request:

.. code-block:: javascript

    {
        "globus_token": "my_custom_globus_scopeed_user_access_token",
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

The custom request is expected to return ``task_id`` at a minimum in a JSON response:

.. code-block::

    {
        "task_id": “abcdeaef-6d04-11e5-ba46-22000b92c6ec"
    }

The task ID returned by the service will be used to monitor the task in Globus.

Configuring a Hub-Managed Service
---------------------------------

The basics of a Hub-Managed service are covered in the `JupyterHub Docs here <https://jupyterhub.readthedocs.io/en/stable/reference/services.html#services>`_.

Creating a service to do custom transfers does not require many additions from the examples shown
there outside of writing the service itself. As stated in the docs, a Hub-Managed service must be built
inside the 'hub' container and specified in the config like so:

.. code-block:: yaml

    hub:
      image:
        name: myorg/my-custom-k8
        tag: latest
        pullPolicy: Always

Flask Example
-------------

A full example which mirrors the Flask Example in JupyterHub is below. Before running the acls service
example, refer to the Globus Auth docs for `Creating a Scope <https://docs.globus.org/api/auth/reference/#create_scope>`_
for your Gloubs App. The client MUST be the one used in the client below. The scope created should be the
same scope configured in JupyterLab for ``GLOBUS_TRANSFER_SUBMISSION_SCOPE``.


.. literalinclude:: ../globus_jupyterlab/tests/k8-testing/hub-service/flask/app.py
   :language: python
