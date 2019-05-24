# Local Setup

## Prerequisites

* JupyterLab (version 0.35.3 or later)
* Node (version 10 or later) and NPM (version 4 or later)
* Create your own Native App registration or use an existing one (to register an app visit the [Globus Developer Pages](https://developers.globus.org)). The app must fit the following criteria:
    * If you are registering a new app, make sure to check the "Will be used by a native application" checkbox
    * Redirect URL: `https://auth.globus.org/v2/web/auth-code`, `https://localhost:8888`
    * Scopes: `urn:globus:auth:scope:transfer.api.globus.org:all`, `urn:globus:auth:scope:search.api.globus.org:all`, `openid`, `profile`, `email`
* Fork this repository. This is needed so that you can use your Client ID (otherwise the extension will not work properly).

## Installation
* In [`client.ts`](src/globus/api/client.ts):
    * Replace the UUID for `CLIENT_ID` with your app's Client ID
    * Make sure that the `REDIRECT_URI` is set to `window.location.href` (without quotes)
* Run the following commands (make sure you are in the root project directory):
    * `npm install`
    * `npm run build`
    * `jupyter labextension install .` (make sure to include the '.' at the end)
    * `jupyter lab build`
    * `jupyter lab`