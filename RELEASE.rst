RELEASE
=======

The release process for Globus JupyterLab is mostly automated through Github Actions,
but still requires manual steps to generate the release notes.

1. Update ``CHANGELOG.md`` and release number in ``package.json``
2. Create a `Github Release <https://github.com/globus/globus-jupyterlab/releases/new>`_

Version
-------

Globus JupyterLab uses semantic style versioning. Package version numbers follow the Python style
guide. Version numbers are identical in Python and NPM, except in betas. ``1.0.0-beta.8`` specified in the ``package.json``
will build to ``1.0.0b8`` in a Python release. Since JupyterLab can be both an NPM or a Python release,
NPM stile are used within the package.json file while python version numbers are generated for Python
releases. Globus JupyterLab continues to use NPM style in the ``package.json`` file, but only does
python releases and uses python style version numbers in the CHANGELOG.

CHANGELOG
---------

The CHANGELOG can be generated using ``standard-version``. Use the following to generate release notes.

.. code-block:: bash

  standard-version --dry-run -p

Don't allow standard-version to tag releases, this is done using the Github interface in step 2. Note also
that standard-version generates slightly incorrect changelog links for betas, using the NPM style instead
of the python style.
