# MyBinderHub Setup
This guide intended to help you get your own MyBinderHub repository working with this extension.

## Installation
1. In [`client.ts`](src/globus/api/client.ts):
    * Replace the UUID for `CLIENT_ID` with your app's Client ID
2. Publish the changes to your repo (using `git add`, `git commit`, and `git push`)
3. Register your Git repo on [MyBinderHub](https://mybinder.org)
    * If you are not familiar with how to do this or encounter any issues, please see the [MyBinderHub Registration Example](../examples/mybinderhub_reg.md) or see the [MyBinderHub Documentation](https://mybinder.readthedocs.io/en/latest/introduction.html).
    * You will need to specify `lab` as the url to open.
