# jupyterlab_globus

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/gneezyn/jupyterlab_globus/master?urlpath=lab)

Jupyterlab Extension that incorporates Globus functionality.

## Setup & Installation
Please see the following table for the file that best fits your purpose.

| File                                      | Description               |
| ----------------------------------------- | ------------------------- |
| [Binder](docs/setups/binder_setup.md)     | For using a Binder repo   |
| [Local](docs/setups/local_setup.md)       | For using a local version |
| [Development](docs/setups/develop.md)     | For developers            |

## Notes
* The Globus Connect Personal feature has been temporarily deleted due to compatibility issues. A later version will support it. Instead of using the convenient Globus Connect Personal file browser from the Globus extension, use the default JupyterLab file browser.
* At this time, the published version of this extension is an older version that no longer works.

## Development

For a development install (requires npm version 4 or later), do the following in the repository directory:

```bash
npm install
npm run build
jupyter labextension link .
```

To rebuild the package and the JupyterLab app:

```bash
npm run build
jupyter lab build
```

## Binder Repo Setup
