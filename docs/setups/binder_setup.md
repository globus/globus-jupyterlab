# Binder Setup

## Prerequisites

* JupyterLab 0.35.3 (or later)
* Create your own Native App registration or use an existing one (to register an app visit the [Globus Developer Pages](https://developers.globus.org)). The app must fit the following criteria:
    * If you are registering a new app, make sure to check the "Will be used by a native application" checkbox
    * Redirect URL: `https://auth.globus.org/v2/web/auth-code`, `https://hub.mybinder.org/hub/login`
    * Scopes: `urn:globus:auth:scope:transfer.api.globus.org:all`, `urn:globus:auth:scope:search.api.globus.org:all`, `openid`, `profile`, `email`
* Fork this repository. This is needed so that you can use your Client ID (otherwise the extension will not work properly).

## Installation
* In [`client.ts`](src/globus/api/client.ts):
    * Replace the UUID for `CLIENT_ID` with your app's Client ID
    * Make sure that the `REDIRECT_URI` is set to `'https://hub.mybinder.org/hub/login'` (with the quotes)
* Publish the changes to your repo (using `git add`, `git commit`, and `git push`)
* Register your Git repo on [Binder](https://mybinder.org)
    * If you are not familiar with how to do this, see the [Binder Registration Example](../examples/binder_reg.md) or see the [Binder Documentation](https://mybinder.readthedocs.io/en/latest/introduction.html).