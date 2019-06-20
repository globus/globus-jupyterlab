# Binder Setup

## Prerequisites

* JupyterLab 0.35.3 (or later)
* Create your own Native App registration or use an existing one (to register an app visit the [Globus Developer Pages](https://developers.globus.org)). The app must fit the following criteria:
    * If you are registering a new app, make sure to check the "Will be used by a native application" checkbox
    * Redirect URL: `https://auth.globus.org/v2/web/auth-code`, `https://hub.mybinder.org/hub/login`
    * Scopes: `urn:globus:auth:scope:transfer.api.globus.org:all`, `urn:globus:auth:scope:search.api.globus.org:all`, `openid`, `profile`, `email`
* Fork this repository. This is needed so that you can use your Client ID (otherwise the extension will not work properly).

## Installation
1. In [`client.ts`](src/globus/api/client.ts):
    * Replace the UUID for `CLIENT_ID` with your app's Client ID
    * Make sure that the `REDIRECT_URI` is set to `'https://hub.mybinder.org/hub/login'` (with the quotes)
2. Publish the changes to your repo (using `git add`, `git commit`, and `git push`)
3. Register your Git repo on [Binder](https://mybinder.org)
    * If you are not familiar with how to do this, see the [Binder Registration Example](../examples/binder_reg.md) or see the [Binder Documentation](https://mybinder.readthedocs.io/en/latest/introduction.html).
    * Once Binder has finished and redirected you, you will need to append `?urlpath=lab` to the url. For example, instead of `https://mybinder.org/v2/gh/<username>/jupyterlab_globus/master`, you will need to go to `https://mybinder.org/v2/gh/<username>/jupyterlab_globus/master?urlpath=lab`.

## Example
To see a working example you can go to the Binder for this repo by following this [link](https://mybinder.org/v2/gh/gneezyn/jupyterlab_globus/master?urlpath=lab). Please be aware that Binder will take a few minutes to build the Binder repo.