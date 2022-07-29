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


Example in Kubernetes
---------------------

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

Shared Mapped Collections
-------------------------

Support is coming soon!


Shared Host Collections
-----------------------

If using a shared collection, special care needs to be taken to ensure the POSIX location accessible
by JupyterLab matches the location accessible by the host Globus Collection. Commonly, the home directory
of the Docker image will be the mount location for external storage, typically ``/home/jovyan``. For Shared collections
which mount a root directory, this can cause a path mis-match where ``/home/jovyan/foo.txt`` accessible from
JupyterLab appears as ``/foo.txt`` on the Globus Collection.

An example is below:

.. code-block:: yaml

  singleuser:
  defaultUrl: "/lab"
  extraEnv:
    JUPYTERHUB_SINGLEUSER_APP: "jupyter_server.serverapp.ServerApp"
    GLOBUS_COLLECTION_ID: "my-globus-collection-uuid"
    GLOBUS_HOST_COLLECTION_BASEPATH: "/"
    GLOBUS_HOST_POSIX_BASEPATH: "/home/jovyan"
    GLOBUS_TOKEN_STORAGE_PATH: "/private/globus_jupyterlab_tokens.json"


Now, using the example above, the GCS storage will allow access to all files on the root of the GCS share at ``/``.
With the share mounted within JupyterLab at ``/home/jovyan``, transferring ``/home/jovyan/foo.txt`` will transfer
``/foo.txt`` at the time of the Globus Transfer.

.. note::
    Saving tokens to ``/private/globus_jupyterlab_tokens.json`` requires a custom Docker container for single users where
    ``/private`` is accessible. Ex: ``RUN mkdir -p /private && chown -R jovyan /private``. Do not use ``/tmp``, it is
    shared across user environments!

See :ref:`config` for the values ``GLOBUS_HOST_POSIX_BASEPATH`` and ``GLOBUS_HOST_COLLECTION_BASEPATH`` for translating
these paths for transfers at runtime.


Storage via NFS
---------------

Storage using NFS on K8s requires custom setup around your k8s cluster. Assuming you
have GCS already setup to share files over NFS, you will need to configure the proper
Persistent Volumes and Persistent Volume Claims. This is documented a little in the
`z2j docs<https://zero-to-jupyterhub.readthedocs.io/en/latest/jupyterhub/customizing/user-storage.html#customizing-user-storage>_`,
but the excercise is left to the user to create the custom k8 PV and PVCs.

An example is below, but you will need to vary this depending on your deployment:

.. code-block:: yaml

    # kubectl apply -f pv.yaml
    apiVersion: v1
    kind: PersistentVolume
    metadata:
    name: nfs
    namespace: lab-test
    spec:
    capacity:
        storage: 1Mi
    accessModes:
        - ReadWriteMany
    nfs:
        server: my-service
        path: "/share"
    mountOptions:
        - nfsvers=4.2

    # kubectl apply -f pvc.yaml
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
    name: nfs
    namespace: lab-test
    spec:
    accessModes:
        - ReadWriteMany
    storageClassName: ""
    resources:
        requests:
        storage: 1Mi
    volumeName: nfs

In order to mount these shares on the user's single-user-server, configure the single-user
storage according to the following:

.. code-block:: yaml

  singleuser:
    storage:
      type: static
      extraLabels: {}
      static:
        pvcName: nfs
        # This will mount under the pv path /share to /share/users/shared
        # subPath: "users/shared"
      capacity: 10Gi

The above setup will mount external NFS storage to user started single-user-server pods, where
``/share/users/shared`` is the actual location on the NFS POSIX machine. In order for this to
match the examples above, make ``/share/users/shared`` the root of your Guest Collection share.
