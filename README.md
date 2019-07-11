# globus_jupyterlab

<!--- [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/gneezyn/jupyterlab_globus/master?urlpath=lab) --->

Jupyterlab Extension that incorporates Globus functionality.

To see a working example you can go to the Binder for this repo by following this [link](https://mybinder.org/v2/gh/gneezyn/jupyterlab_globus/master?urlpath=lab). Please be aware that the MyBinderHub repo may take several minutes to launch.

## Prerequisites
This extension requires JupyterLab 0.35.3 (or later). In addition, you will also need the following if you want to use your own Native App or implement other changes:
* Create your own Native App registration or use an existing one (to register an app visit the [Globus Developer Pages](https://developers.globus.org)). The app must fit the following criteria:
    * If you are registering a new app, make sure to check the "Will be used by a native application" checkbox
    * Redirect URL: `https://auth.globus.org/v2/web/auth-code`
    * Scopes: `urn:globus:auth:scope:transfer.api.globus.org:all`, `urn:globus:auth:scope:search.api.globus.org:all`, `openid`, `profile`, `email`
* Fork this repository. This is needed so that you can use your Client ID (otherwise the extension will not work properly).

## Setup & Developer Guides
To avoid confusion, the setup instructions and developer information have been moved to the **docs** folder. Please see the following list for the file that best fits your purpose.

* [MyBinderHub Setup](docs/setups/mybinderhub_setup.md) - setup instructions for the MyBinderHub repo version
    * Recommended for practical use and users familiar with the extension.
* [Local Setup](docs/setups/local_setup.md) - setup instructions for the local version
    * Recommended for developers
* [Development Relevant Info](docs/develop/) - contains information that is meant for anyone wanting to further develop this extension

## Notes
* The Globus Connect Personal feature has been temporarily disabled due to compatibility issues. A later version will support it. Instead of using the convenient Globus Connect Personal file browser from the Globus extension, use the default JupyterLab file browser.
* At this time, the [npm package](https://www.npmjs.com/package/jupyterlab_globus) for this extension is an older version that no longer works.
