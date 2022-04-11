# Local Setup


## Installation

### Quick Start
The following describes the series of steps needed to install and run this extension for the first time.

1. Run the following commands (make sure you are in the root project directory):
    1. `pip install jupyterlab jupyter-packaging`
    2. `jupyter labextension develop . --overwrite` (make sure to include the '.' at the end so that the local version is installed)
    3. `jlpm run build`
    4. `jupyter lab`

