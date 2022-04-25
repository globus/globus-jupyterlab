import { JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';
import { IFileBrowserFactory } from "@jupyterlab/filebrowser";
import { MainAreaWidget } from '@jupyterlab/apputils';
import { PageConfig } from '@jupyterlab/coreutils';
import { reactIcon } from '@jupyterlab/ui-components';

import { GlobusIcon } from './utilities';
import { GlobusWidget } from './widget';
import { requestAPI } from './handler';

import '../style/index.css';

const addJupyterCommands = (app: JupyterFrontEnd, factory: IFileBrowserFactory, commands: Array<any>) => {
  for (let command of commands) {
    app.commands.addCommand(command.command, {
      label: command.label,
      caption: command.caption,
      icon: GlobusIcon,
      execute: async () => {
        var files = factory.tracker.currentWidget.selectedItems();
        var jupyterToken = PageConfig.getToken();
        var label = 'Globus Jupyterlab Transfer'

        let jupyterItems = [],
          fileCheck = true;
        while (fileCheck) {
          let file = files.next();
          if (file) {
            jupyterItems.push(file);
          } else {
            fileCheck = false;
          }
        }

        // GET config payload which contains basic auth data
        const config = await requestAPI<any>('config');
        const isAuthenticated = config.is_logged_in;

        // Start creating the widget, but don't attach unless authenticated
        const content = new GlobusWidget(config, jupyterToken, jupyterItems);
        const widget = new MainAreaWidget<GlobusWidget>({ content });
        widget.title.label = label;
        widget.title.icon = reactIcon;

        if (isAuthenticated) {
          app.shell.add(widget, 'main');
        } else {
          // Poll for successful authentication. 
          let authInterval = window.setInterval(async () => {
            const config = await requestAPI<any>('config');
            const isAuthenticated = config.is_logged_in;

            if (isAuthenticated) {
              app.shell.add(widget, 'main');
              clearInterval(authInterval);
            }
          }, 500);
          window.open('/globus-jupyterlab/login', 'Globus Login', 'height=600,width=800').focus();
        }
      },
    });
  }
};

/**
 * Globus plugin
 */
export const globus: JupyterFrontEndPlugin<void> = {
    id: '@jupyterlab/globus_jupyterlab',
    autoStart: true,
    requires: [IFileBrowserFactory],
    activate: activateGlobus
};

async function activateGlobus(app: JupyterFrontEnd, factory: IFileBrowserFactory) {
    console.log('Globus Jupyterlab Extension Activated!');

    // GET request
    try {
      const data = await requestAPI<any>('config');
      console.log('Fetching basic data about the notebook server environment:', data);

      /*
      Commands to initiate a Globus Transfer. 
      */
      let commands = [
        {
          command: 'globus-jupyterlab-transfer/context-menu:open',
          label: 'Initiate Globus Transfer',
          caption: 'Login with Globus to initiate transfers',
        },
      ];
      addJupyterCommands(app, factory, commands);

    } catch (reason) {
      console.error(`Error on GET /globus_jupyterlab/config.\n${reason}`);
    }
}

/**
 * Export the plugin as default.
 */
export default globus;
