import {ILayoutRestorer, JupyterFrontEnd, JupyterFrontEndPlugin} from '@jupyterlab/application';
import '../style/index.css';
import {GlobusHome} from "./globus/home";
import {IDocumentManager} from '@jupyterlab/docmanager';
import {IFileBrowserFactory} from "@jupyterlab/filebrowser";
import {GlobusWidgetManager} from "./globus/widget_manager";
import {GlobusContextMenu} from "./globus/context_menu";

/**
 * Globus plugin
 */
export const globus: JupyterFrontEndPlugin<void> = {
    id: '@jupyterlab/globus_jupyterlab',
    autoStart: true,
    requires: [IDocumentManager, ILayoutRestorer, IFileBrowserFactory],
    activate: activateGlobus
};

function activateGlobus(app: JupyterFrontEnd, manager: IDocumentManager, restorer: ILayoutRestorer, factory: IFileBrowserFactory) {
    // Writes and executes a command inside of the default terminal in JupyterLab.
    // console.log(app.info);
    // app.serviceManager.terminals.startNew().then(session => {
    //     let request = `http POST ${window.location.href}/static body="$(printenv)" 'Authorization:token ${ServerConnection.defaultSettings.token}'\r`;
    //     session.send({ type: 'stdin', content: [request]});
    // });
    console.log('Globus Jupyterlab Extension Activated!');


    let widgetManager: GlobusWidgetManager = new GlobusWidgetManager(app, manager, factory);
    // Note: This path is hardcoded as a prototype. Previously, the serverRoot could be determined
    // from the app. This changed in the last version, and now MUST be fetched from a server plugin.
    let contextMenu = new GlobusContextMenu('/Users/nick/globus/globus_jupyterlab', factory)
    let home: GlobusHome = new GlobusHome(widgetManager);
    restorer.add(home, 'globus-home');
    app.shell.add(home, 'left');
    app.commands.addCommand('globus-jupyterlab/context-menu:open', contextMenu.options);
}

/**
 * Export the plugin as default.
 */
export default globus;
