import { ReactWidget } from '@jupyterlab/apputils';

import React, { useEffect, useState } from 'react';


const FileBrowser = (props: any): JSX.Element => {
  const [fileInfoArray, setFileInfoArray] = useState([])
  useEffect(() => {
    getFileInfo();
  }, [props.files]);

  const getFileInfo = async () => {
    let fileInfoArrayTemp = []
    for (let file of props.files) {
      let response = await fetch(`/api/contents/${file.path}`, {
        headers: {
          'Accept': 'application/json',
          'Authorization': `token ${props.jupyterToken}`,
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        let fileInfo = await response.json();
        fileInfoArrayTemp.push(fileInfo);
      }
    }
    setFileInfoArray(fileInfoArrayTemp);
  }

  return (
    <div>
      <p>You want to transfer the following {props.transferDirection == 'to_collection' ? 'to' : 'from'} a Globus Collection</p>
      {fileInfoArray.length && 
        <div>
          <hr />
          {fileInfoArray.map((file) => {
            console.log(file.content);
            return (
              <div key={file.name}> 
                <span><strong>Type:</strong> {file.type}</span><br />
                <span><strong>Name:</strong> {file.name}</span><br />
                <span><strong>Path:</strong> {file.path}</span><br />
                {file.type !== 'directory' && 
                  <span><strong>Content:</strong> {file.content}</span>
                }
                <hr />
              </div>
            )
          })}
        </div>
      }
    </div>
  )
};

export class GlobusWidget extends ReactWidget {
  fileArray: Array<string>;
  jupyterToken: string;
  transferDirection: string;
  constructor(jupyterToken = '', fileArray = [], transferDirection = '') {
    super();

    this.fileArray = fileArray;
    this.jupyterToken = jupyterToken;
    this.transferDirection = transferDirection;
    this.addClass('jp-ReactWidget');
  }

  render(): JSX.Element {
    return (
      <FileBrowser files={this.fileArray} jupyterToken={this.jupyterToken} transferDirection={this.transferDirection} />
    );
  }
}
