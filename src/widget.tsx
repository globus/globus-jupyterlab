import { getBaseURL } from './utilities';
import { HashRouter, Route, Switch } from 'react-router-dom';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';
import { ReactWidget } from '@jupyterlab/apputils';
import React, { useEffect, useState } from 'react';
import { RecoilRoot, useSetRecoilState } from 'recoil';
import { requestAPI } from './handler';

import EndpointSearch from './components/EndpointSearch';

import { ConfigAtom } from './components/GlobusObjects';

import '@fortawesome/fontawesome-free/css/all.min.css';
import 'bootstrap/dist/css/bootstrap.min.css';

// Import specific bootstrap javascript plugins
import 'bootstrap/js/dist/alert.js';

const App = (props: any): JSX.Element => {
  // Local state values
  const [selectedJupyterItems, setSelectedJupyterItems] = useState({ isEmpty: true });

  // Global Recoil state values
  const setConfig = useSetRecoilState(ConfigAtom);

  useEffect(() => {
    setConfig(props.config);
  }, [props.config]);

  useEffect(() => {
    getJupyterItems();
  }, [props.jupyterItems]);

  const getJupyterItems = async () => {
    let directories = [];
    let files = [];

    let selectedJupyterItemsTemp = {};

    for (let file of props.jupyterItems) {
      try {
        let response = await fetch(getBaseURL(`api/contents/${file.path}`), {
          headers: {
            Accept: 'application/json',
            Authorization: `token ${props.jupyterToken}`,
            'Content-Type': 'application/json',
          },
        });

        let temp = await response.json();
        if (temp.type == 'directory') {
          directories.push(temp);
        } else {
          files.push(temp);
        }
      } catch (error) {
        console.log(error);
      }
    }

    selectedJupyterItemsTemp['directories'] = directories;
    selectedJupyterItemsTemp['files'] = files;

    // If we have any file or folder, the payload is not empty
    if (directories.length || files.length) {
      selectedJupyterItemsTemp['isEmpty'] = false;
    }

    // Transfer direction inferred from selected files/folders
    if ((files.length && directories.length) || (files.length && !directories.length)) {
      selectedJupyterItemsTemp['transferDirection'] = 'toEndpoint';
    } else {
      selectedJupyterItemsTemp['transferDirection'] = 'toFromEndpoint';
    }

    //@ts-ignore
    setSelectedJupyterItems(selectedJupyterItemsTemp);
  };

  const handleLogout = async (event) => {
    event.preventDefault();
    await requestAPI<any>('logout');
    window.open('https://globus.org/logout', 'Logout of Globus', 'height=600,width=800').focus();
    window.location.reload();
  };
  return (
    <div className='container pt-5'>
      <div className='row'>
        <div className='col-8'>
          <a href='#' onClick={handleLogout}>
            <i className='fa-solid fa-arrow-right-from-bracket'></i> Logout of Globus
          </a>

          <hr className='mb-3 mt-3' />
        </div>
      </div>
      {!selectedJupyterItems['isEmpty'] ? (
        <EndpointSearch factory={props.factory} selectedJupyterItems={selectedJupyterItems} />
      ) : (
        <p className='fw-bold text-danger'>No files selected</p>
      )}
    </div>
  );
};

export class GlobusWidget extends ReactWidget {
  config: Object;
  factory: IFileBrowserFactory;
  jupyterItems: Array<string>;
  jupyterToken: string;
  constructor(config = {}, factory = null, jupyterToken = '', jupyterItems = []) {
    super();

    this.config = config;
    this.factory = factory;
    this.jupyterItems = jupyterItems;
    this.jupyterToken = jupyterToken;
    this.addClass('jp-ReactWidget');
  }

  render(): JSX.Element {
    return (
      <HashRouter>
        <RecoilRoot>
          <Switch>
            <Route
              path='/'
              render={(props) => {
                return (
                  <App
                    {...props}
                    config={this.config}
                    factory={this.factory}
                    jupyterItems={this.jupyterItems}
                    jupyterToken={this.jupyterToken}
                  />
                );
              }}
            />
          </Switch>
        </RecoilRoot>
      </HashRouter>
    );
  }
}
