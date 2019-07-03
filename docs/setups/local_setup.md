# Local Setup


## Installation

### Quick Start
The following describes the series of steps needed to install and run this extension for the first time.

1. Run the following commands (make sure you are in the root project directory):
    1. `npm install`
    2. `npm run build`
    3. `jupyter labextension install .` (make sure to include the '.' at the end so that the local version is installed)
    4. `jupyter lab build`
    5. `jupyter lab`

### Optional
If you want to use your own NativeApp then in [client.ts](src/globus/api/client.ts), replace the UUID for `CLIENT_ID` with your app's Client ID.

### For Developers
The approach described above is a good place to start, but is not the best approach if you are planning to frequently modify the code. The following steps describe one possible approach that is better suited for development (and debugging) purposes. To avoid repetition, it assummes that the previously mentioned changes to [client.ts](src/globus/api/client.ts) have already been made (see step 1 in the Quick Start section). 

1. In a terminal, navigate to the project's root directory
2. Run `npm install` ONLY if you meet at least one of the following conditions:
    * You have not previously run `npm install`.
    * You have added new dependencies that need to be installed.
    * The project dependencies have changed since you last ran `npm install`.
3. If this is your first time using the extension then run the following commands:
    1. `npm run build`
    2. `jupyter labextension install .` (make sure to include the '.' at the end so that the local version is installed)
    3. `jupyter lab build`
4. Run `npm run watch`
    * This is especially useful in identifying errors or other issues that jupyter might not mention.
    * When you go on to the next step, make sure that this command keeps running.
5. In a new terminal window or tab (also in the project's root directory) run `jupyter lab --watch`.

Steps 4 and 5 cause the installed extension to be updated every time you make and save a change to the local code (you will still need to reload the page).
