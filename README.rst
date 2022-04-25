Globus JupyterLab
=================


.. |docs| image:: https://readthedocs.org/projects/globus-jupyterlab/badge/?version=docs
   :target: https://globus-jupyterlab.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/globus/globus-jupyterlab/actions/workflows/quality.yml/badge.svg
    :target: https://github.com/globus-jupyterlab/globus-jupyterlab/actions/workflows/

.. image:: https://img.shields.io/pypi/v/globus-jupyterlab.svg
    :target: https://pypi.python.org/pypi/globus-jupyterlab

.. image:: https://img.shields.io/pypi/wheel/globus-jupyterlab.svg
    :target: https://pypi.python.org/pypi/globus-jupyterlab

Globus Jupyterlab is an extension to Jupyterlab for easily submitting Globus Transfers
within a running lab environment. Integration within the Jupyterlab filemanager makes
starting transfers just a few clicks away!

Install with the following: 

.. code-block:: bash

    pip install globus-jupyterlab

For information on usage, see the `Read-The-Docs <https://globus-jupyterlab.readthedocs.io/en/main/#>`_.

Developing
----------

For development, use the following instructions: 

.. code-block:: bash

    # install the extension in editable mode
    python -m pip install -e .

    # install your development version of the extension with JupyterLab
    jupyter labextension develop . --overwrite

    # build the TypeScript source after making changes
    jlpm run build

    # start JupyterLab
    jupyter lab
