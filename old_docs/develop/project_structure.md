# Project Structure
The descriptions below are brief and are only meant to provide an overview of the project structure. Only the files and directories in the **src** directory are described here.

## Globus Directory (src/globus/)

### API Directory (src/globus/api/)
Main directory for defining the API. Contains the following files:
* [Client](../../../src/globus/api/client.ts)
    * Implements various functions and is mostly responsible for retrieving access tokens and loging the user out of Globus.
* [Models](../../../src/globus/api/models.ts)
    * Defines the various, Globus-specific, interfaces used throughout the project.
* [Search](../../../src/globus/api/search.ts)
    * Implements various functions for the Search feature, which allows users to search for endpoints.
    * Used by the [Search](../../../src/globus/widgets/search.ts) widget.
* [Transfer](../../../src/globus/api/transfer.ts)
    * Implements various functions for the Transfer feature, which allows users to transfer files from one endpoint to another.
    * Used by both the [Activity](../../../src/globus/widgets/activity.ts) and [File Manager](../../../src/globus/widgets/file_manager.ts) widgets.

### Widgets Directory (src/globus/widgets/)
Main directory for defining the widgets. Contains the following files:
* [Activity](../../../src/globus/widgets/activity.ts)
    * Implements the GlobusWidget, which allows users to see the list of tasks.
* [File Manager](../../../src/globus/widgets/file_manager.ts)
    * Implements the "File Manager" feature, which allows users to manipulate files in various ways (i.e., create new folder, delete a file).
    * Includes the ability to create shared endpoints and make transfer requests.
* [Globus Connect Personal](../../../src/globus/widgets/globus_connect_personal.ts)
    * The Globus Connect Personal widget is currently disabled.
* [Search](../../../src/globus/widgets/search.ts)
    * Implements the "Search" feature, which allows users to search for endpoints.
    * Includes search indexes.

#### [Home](../../../src/globus/home.ts)
Acts as the main "home" page for the extension. Responsible for handling Globus sign in.

#### [Widget Manager](../../../src/globus/widget_manager.ts)
As the name implies, this file defines the WidgetManager class, which is responsible for managing all of the widgets. This includes actions such as creation, initialization, and switching between the widgets.

## Other Files

##### [Index](../../../src/index.ts)
This file is the starting point for the extension.

#### [Utils](../../../src/utils.ts)
This file defines various constants and functions that are used throughout the project. It also has a corresponding [test file](../../../src/utils.spec.ts).