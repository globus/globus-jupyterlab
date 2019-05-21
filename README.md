# jupyterlab_globus

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/gneezyn/jupyterlab_globus/binderhub)

Incorporates Globus functionality. Compatible with Windows, iOS and Linux.
For snapshots of the project visit the following link and see slide 24 and onwards!

https://www.slideshare.net/ianfoster/scaling-collaborative-data-science-with-globus-and-jupyter.


## Prerequisites

* JupyterLab 0.34.7
* Create your own Native App registration for use with the examples. Visit the [Globus Developer Pages](https://developers.globus.org) to register an App.
    * When registering the App you'll be asked for some information, including the redirect URL and any scopes you will be requesting.
        * Check the "Will be used by a native application" checkbox
        * Redirect URL: `https://auth.globus.org/v2/web/auth-code`, `https://localhost:8888`
        * Scopes: `urn:globus:auth:scope:transfer.api.globus.org:all`, `urn:globus:auth:scope:search.api.globus.org:all`, `openid`, `profile`, `email`
* Replace the UUID for `CLIENT_ID` in [`client.ts`](src/globus/api/client.ts).

## Installation

```bash
jupyter labextension install jupyterlab_globus
jupyter lab build
jupyter lab
```

## Notes

The Globus Connect Personal feature has been temporarily deleted due to compatibility issues. A later version will support it. Instead of using the convenient Globus Connect Personal file browser from the Globus extension, use the default JupyterLab file browser.

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

