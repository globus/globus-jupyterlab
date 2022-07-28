JupyterHub
==========

For the most part, running JupyterLab in a Hub environment is the same as running JupyterLab
locally on a workstation.

Users can transfer to or from any accessible Globus endpoint or collection. As a convenience,
Globus JupyterLab will automatically detect a local, running Globus Connect Personal endpoint.
Globus Connect Personal may be downloaded from the Globus web application. https://app.globus.org/file-manager/gcp

Globus Connect Server collections cannot be determined automatically.  These collections will need to be speficied
manually either directly as env variables in the environment, or by `OAuthenticator <https://oauthenticator.readthedocs.io/en/latest/getting-started.html#globus-scopes-and-transfer>`_

For example:

.. code-block:: bash

   export GLOBUS_COLLECTION_ID='MyCollectionUUID'

See :ref:`config` for a full list of config options.

Mapped Collections
------------------

Support is coming soon!


Guest Collections
-----------------

Guest Collections are typically mounted filesystems over NFS. The same file viewed by the user in Globus JupyterLab may have a differenet path
viewed through Globus Connect Server.

For example, a GCS share may be mounted inside a single user server at ``/home/jovyan``. A file in a single user server in Globus
JupyterLab will be ``/home/jovyan/foo.txt``, but can only be accessed from the Globus Collection as ``/foo.txt``.
Setting ``GLOBUS_HOST_POSIX_BASEPATH`` to ``/home/jovyan`` fixes this mismatch. Now when Globus JupyterLab submits a transfer,
paths will be translated to "GCS" paths, transferring ``/foo.txt`` instead of ``/home/jovyan/foo.txt``.

``GLOBUS_HOST_COLLECTION_BASEPATH`` is also available if you want Globus JupyterLab to transfer files to a subfolder inside
a Guest Collection share.

See :ref:`config` for more info on ``GLOBUS_HOST_POSIX_BASEPATH`` and ``GLOBUS_HOST_COLLECTION_BASEPATH``.


.. warning::
    User tokens are stored in the user's home directory by default. This path needs to be changed if the Guest Collection share
    could be visible to other users. See the :ref:`config` option GLOBUS_TOKEN_STORAGE_PATH.


Kubernetes
----------

The Zero-To-JupyterHub the single-user-server is typically run on a pod separate from the hub,
and so needs to be configured accordingly. See the `User Environment Documentation <https://zero-to-jupyterhub.readthedocs.io/en/latest/jupyterhub/customizing/user-environment.html>`_

.. code-block:: yaml

    singleuser:
        extraEnv:
            GLOBUS_COLLECTION_ID: "MyCollectionUUID"

    hub:
        extraConfig:
            10-set-local-globus-collection: |
                # This is only possible if users login via the Globus OAuthenticator.
                # GLOBUS_COLLECTION_ID will take precedence if both are present.
                c.OAuthenticator.globus_local_endpoint = '1346ef68-d9b8-4757-a537-47cefb7698e8'


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
