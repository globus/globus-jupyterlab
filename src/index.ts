import {ILayoutRestorer, JupyterFrontEnd, JupyterFrontEndPlugin} from '@jupyterlab/application';
import '../style/index.css';
import {GlobusHome} from "./globus/home";
import {IDocumentManager} from '@jupyterlab/docmanager';
import {IFileBrowserFactory} from "@jupyterlab/filebrowser";
import {GlobusWidgetManager} from "./globus/widget_manager";

import { requestAPI } from './handler';
/**
 * Globus plugin
 */
export const globus: JupyterFrontEndPlugin<void> = {
    id: '@jupyterlab/globus_jupyterlab',
    autoStart: true,
    requires: [IDocumentManager, ILayoutRestorer, IFileBrowserFactory],
    activate: activateGlobus
};

async function activateGlobus(app: JupyterFrontEnd, manager: IDocumentManager, restorer: ILayoutRestorer, factory: IFileBrowserFactory) {
    // Writes and executes a command inside of the default terminal in JupyterLab.
    // console.log(app.info);
    // app.serviceManager.terminals.startNew().then(session => {
    //     let request = `http POST ${window.location.href}/static body="$(printenv)" 'Authorization:token ${ServerConnection.defaultSettings.token}'\r`;
    //     session.send({ type: 'stdin', content: [request]});
    // });
    console.log('Globus Jupyterlab Extension Activated!');


    let widgetManager: GlobusWidgetManager = new GlobusWidgetManager(app, manager, factory);
    let home: GlobusHome = new GlobusHome(widgetManager);
    restorer.add(home, 'globus-home');
    app.shell.add(home, 'left');

    console.log('JupyterLab extension server-extension-example is activated!');

    // GET request
    try {
      const data = await requestAPI<any>('config');
      console.log('Fetching basic data about the notebook server environment:', data);
    } catch (reason) {
      console.error(`Error on GET /globus_jupyterlab/config.\n${reason}`);
    }
}

/**
 * Export the plugin as default.
 */
export default globus;
