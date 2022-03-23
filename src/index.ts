import { buildIcon, reactIcon } from '@jupyterlab/ui-components';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';
import { ILayoutRestorer, JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';
import { MainAreaWidget } from '@jupyterlab/apputils';
import { PageConfig } from '@jupyterlab/coreutils';

import { GlobusHome } from './globus/home';
import { GlobusWidgetManager } from './globus/widget_manager';
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
        var label =
          command.transfer_direction == 'to_collection'
            ? 'Transfer to a Globus Collection'
            : 'Transfer from a Globus Collection';

        let fileArray = [],
          fileCheck = true;
        while (fileCheck) {
          let file = files.next();
          if (file) {
            fileArray.push(file);
          } else {
            fileCheck = false;
          }
        }

        const config = await requestAPI<any>('config');
        const isAuthenticated = config.is_logged_in;

        if (isAuthenticated) {
          const content = new GlobusWidget(jupyterToken, fileArray, command.transfer_direction);
          const widget = new MainAreaWidget<GlobusWidget>({ content });
          widget.title.label = label;
          widget.title.icon = reactIcon;
          app.shell.add(widget, 'main');
        } else {
          let authInterval = window.setInterval(async () => {
            const config = await requestAPI<any>('config');
            const isAuthenticated = config.is_logged_in;

            const content = new GlobusWidget(jupyterToken, fileArray, command.transfer_direction);
            const widget = new MainAreaWidget<GlobusWidget>({ content });
            widget.title.label = label;
            widget.title.icon = reactIcon;

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
  activate: activateGlobus,
};

async function activateGlobus(
  app: JupyterFrontEnd,
  manager: IDocumentManager,
  restorer: ILayoutRestorer,
  factory: IFileBrowserFactory
) {
  console.log('Globus Jupyterlab Extension Activated!');

  let widgetManager: GlobusWidgetManager = new GlobusWidgetManager(app, manager, factory);
  let home: GlobusHome = new GlobusHome(widgetManager);
  restorer.add(home, 'globus-home');
  app.shell.add(home, 'left');

  console.log('JupyterLab extension server-extension-example is activated!');

  // Ask for permission before starting transfers on startup.
  const i_want_to_start_a_transfer_to_my_local_home_directory = false;
  // GET request
  try {
    const data = await requestAPI<any>('config');
    console.log('Fetching basic data about the notebook server environment:', data);
    const transferRequest = {
      //Globus Tutorial Endpoint 1
      source_endpoint: 'ddb59aef-6d04-11e5-ba46-22000b92c6ec',
      destination_endpoint: data.collection_id,
      transfer_items: [
        {
          source_path: '/share/godata',
          destination_path: '~/',
          recursive: true,
        },
      ],
    };

    if (data.is_logged_in && i_want_to_start_a_transfer_to_my_local_home_directory) {
      submitTransfer(transferRequest);
    } else if (!data.is_logged_in) {
      console.log('You are not logged in, visit http://localhost:8888/globus-jupyterlab/login to login');
    } else if (!i_want_to_start_a_transfer_to_my_local_home_directory) {
      // Consent is important
      console.log('Aborting Transfer to your local home directory! Check index.ts for more info!');
    }
  } catch (reason) {
    console.error(`Error on GET /globus_jupyterlab/config.\n${reason}`);
  }

  /*
    Commands to initiate a Globus Transfer. 
  */
  addJupyterCommands(app, factory, [
    {
      command: 'globus-jupyterlab-to-collection/context-menu:open',
      label: 'Initiate File Transfer to Globus Collection',
      caption: 'Login with Globus to initiate transfers',
      transfer_direction: 'to_collection',
    },
    {
      command: 'globus-jupyterlab-from-collection/context-menu:open',
      label: 'Initiate File Transfer from Globus Collection',
      caption: 'Login with Globus to initiate transfers',
      transfer_direction: 'from_collection',
    },
  ]);
}

async function submitTransfer(transferRequest) {
  try {
    const reply = await requestAPI<any>('submit_transfer', {
      body: JSON.stringify(transferRequest),
      method: 'POST',
    });
    console.log(reply);
  } catch (reason) {
    console.error(`Error on POST /jlab-ext-example/hello ${transferRequest}.\n${reason}`);
  }
}

/**
 * Export the plugin as default.
 */
export default globus;
