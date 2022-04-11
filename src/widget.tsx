import { HashRouter, Route, Switch } from 'react-router-dom';
import { ReactWidget } from '@jupyterlab/apputils';
import React, { useEffect, useState } from 'react';
import { RecoilRoot, useSetRecoilState } from 'recoil';

import EndpointSearch from './components/EndpointSearch';

import { ConfigAtom } from './components/GlobusObjects';

import '@fortawesome/fontawesome-free/css/all.min.css';
import 'bootstrap/dist/css/bootstrap.min.css';

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
        let response = await fetch(`/api/contents/${file.path}`, {
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

  return (
    <div className='container pt-5'>
      {!selectedJupyterItems['isEmpty'] ? (
        <EndpointSearch selectedJupyterItems={selectedJupyterItems} />
      ) : (
        <p className='fw-bold text-danger'>No files selected</p>
      )}
    </div>
  );
};

export class GlobusWidget extends ReactWidget {
  config: Object;
  jupyterItems: Array<string>;
  jupyterToken: string;
  constructor(config = {}, jupyterToken = '', jupyterItems = []) {
    super();

    this.config = config;
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
