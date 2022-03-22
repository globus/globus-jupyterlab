import { ReactWidget } from '@jupyterlab/apputils';

import React from 'react';

/**
 * React component for a counter.
 *
 * @returns The React component
 */

const FileBrowser = (props: any): JSX.Element => {
  return <p>Hello, World!</p>;
};

export class GlobusWidget extends ReactWidget {
  constructor() {
    super();

    this.addClass('jp-ReactWidget');
  }

  render(): JSX.Element {
    return <FileBrowser />;
  }
}
