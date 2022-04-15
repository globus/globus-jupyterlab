import { buildIcon, reactIcon } from '@jupyterlab/ui-components';
import {ILayoutRestorer, JupyterFrontEnd, JupyterFrontEndPlugin} from '@jupyterlab/application';
import {GlobusHome} from "./globus/home";
import {IDocumentManager} from '@jupyterlab/docmanager';
import {IFileBrowserFactory} from "@jupyterlab/filebrowser";
import {GlobusWidgetManager} from "./globus/widget_manager";
import { MainAreaWidget } from '@jupyterlab/apputils';
import { PageConfig } from '@jupyterlab/coreutils';

import { GlobusWidget } from './widget';
import { requestAPI } from './handler';

import '../style/index.css';


const addJupyterCommands = (app: JupyterFrontEnd, factory: IFileBrowserFactory, commands: Array<any>) => {
  for (let command of commands) {
    app.commands.addCommand(command.command, {
      label: command.label,
      caption: command.caption,
      icon: buildIcon,
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
          window.open('/globus-jupyterlab/login', '_blank');
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

    // Ask for permission before starting transfers on startup.
    const i_want_to_start_a_transfer_to_my_local_home_directory = false
    // GET request
    try {
      const data = await requestAPI<any>('config');
      console.log('Fetching basic data about the notebook server environment:', data);

      const operation_ls = await requestAPI<any>('operation_ls?endpoint=ddb59aef-6d04-11e5-ba46-22000b92c6ec');
      console.log('Info on collection', operation_ls);

      const endpoint_search = await requestAPI<any>('endpoint_search?filter_fulltext=tutorial');
      console.log('Endpoint Search: ', endpoint_search);

      const endpoint_autoactivate = await requestAPI<any>('endpoint_autoactivate', {
        body: JSON.stringify({'endpoint_id': 'ddb59aef-6d04-11e5-ba46-22000b92c6ec'}),
        method: 'POST',
      });
      console.log(endpoint_autoactivate);

      const transferRequest = {
        //Globus Tutorial Endpoint 1
        'source_endpoint': 'ddb59aef-6d04-11e5-ba46-22000b92c6ec',
        'destination_endpoint': data.collection_id,
        'transfer_items': [{
          'source_path': '/share/godata',
          'destination_path': '~/',
          'recursive': true,
        }]
      };
      
      if (data.is_logged_in && i_want_to_start_a_transfer_to_my_local_home_directory) {
        submitTransfer(transferRequest)
      } else if (!data.is_logged_in) {
        console.log('You are not logged in, visit http://localhost:8888/globus-jupyterlab/login to login')
      } else if (!i_want_to_start_a_transfer_to_my_local_home_directory) {
        // Consent is important
        console.log('Aborting Transfer to your local home directory! Check index.ts for more info!')
      }

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

async function submitTransfer(transferRequest) {
  try {
    const reply = await requestAPI<any>('submit_transfer', {
      body: JSON.stringify(transferRequest),
      method: 'POST',
    });
    console.log(reply);
  } catch (reason) {
    console.error(
      `Error on POST /jlab-ext-example/hello ${transferRequest}.\n${reason}`
    );
  }
}

/**
 * Export the plugin as default.
 */
export default globus;
