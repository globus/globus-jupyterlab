import { Link } from 'react-router-dom';
import React, { useEffect, useState } from 'react';
import { requestAPI } from '../handler';
import { useHistory, useParams } from 'react-router-dom';
import { useRecoilValue } from 'recoil';

import { ConfigAtom } from './GlobusObjects';

const Endpoint = (props) => {
  // Local State
  const [apiError, setAPIError] = useState(null);
  const [endpointList, setEndpointList] = useState({ DATA: [], path: null });
  const [endpoint, setEndpoint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedEndpointItems, setSelectedEndpointItems] = useState([]);
  const [transfer, setTransfer] = useState(null);
  const [transferDirection, setTransferDirection] = useState(null);

  // Recoil (global) State
  const config = useRecoilValue(ConfigAtom);

  // React Router history and params
  let history = useHistory();
  let params = useParams();
  let endpointID = params.endpointID;
  let path = params.path;

  // ComponentDidMount Functions
  useEffect(() => {
    getEndpoint(endpointID);
  }, [endpointID]);

  useEffect(() => {
    listEndpointItems(endpointID, path);
  }, [endpointID, path]);

  const getEndpoint = async (endpointID) => {
    try {
      let response = await fetch(`/globus-jupyterlab/endpoint_detail?endpoint=${endpointID}`, {
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
      });

      let endpoint = await response.json();
      if ('error' in endpoint) {
        throw endpoint;
      }
      setEndpoint(endpoint);
    } catch (error) {
      setAPIError(error);
    }
  };

  const listEndpointItems = async (endpointID, path = null) => {
    setAPIError(null);
    setEndpointList({ DATA: [], path: null });
    setLoading(true);
    try {
      let url = `/globus-jupyterlab/operation_ls?endpoint=${endpointID}&show_hidden=0`;
      if (path) {
        url = `${url}&path=${path}`;
      }
      const response = await fetch(url, {
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
      });

      const listItems = await response.json();
      if ('error' in listItems) {
        throw listItems;
      }
      setEndpointList(listItems);
    } catch (error) {
      /* Note: This probably isn't a great UX to simply pop up a login page, but it
      does demonstrate the base functionality for picking endpoints */
      if ('login_url' in error) {
        window.open(error.login_url, 'Globus Login', 'height=600,width=800').focus();
      }
      setAPIError(error);
    }
    setLoading(false);
  };

  // Event Handlers
  const handleEndpointItemSelect = (event) => {
    if (event.target.checked) {
      setSelectedEndpointItems((selectedEndpointItems) => {
        return [JSON.parse(event.target.value), ...selectedEndpointItems];
      });
    } else {
      const removeItem = JSON.parse(event.target.value);
      const index = selectedEndpointItems
        .map((item) => {
          return item.name;
        })
        .indexOf(removeItem.name);
      if (index > -1) {
        selectedEndpointItems.splice(index, 1);
        setSelectedEndpointItems(selectedEndpointItems);
      }
    }
  };

  const handleTransferDirection = (event) => {
    setTransferDirection(event.currentTarget.value);
  };

  const handleTransferRequest = async (event) => {
    event.preventDefault();
    setAPIError(null);
    setLoading(true);
    setTransfer(null);

    var transferItems = [];

    var sourceEndpoint = transferDirection == 'transfer-to-jupyter' ? endpoint.id : config.collection_id;
    var destinationEndpoint = transferDirection == 'transfer-to-jupyter' ? config.collection_id : endpoint.id;

    if (transferDirection == 'transfer-from-jupyter') {
      if (selectedEndpointItems.length > 1) {
        setAPIError({ error: 'Please only select one remote directory to transfer data to' });
      }

      // Loop through selectedJupyterItems from props
      if (props.selectedJupyterItems.directories.length) {
        for (let directory of props.selectedJupyterItems.directories) {
          let destinationPath = selectedEndpointItems.length
            ? `${endpointList.path}${selectedEndpointItems[0].name}/${directory.path}`
            : `${endpointList.path}${directory.path}`;

          transferItems.push({
            source_path: `${config.collection_base_path}/${directory.path}`,
            destination_path: destinationPath,
            recursive: true,
          });
        }
      }

      if (props.selectedJupyterItems.files.length) {
        for (let file of props.selectedJupyterItems.files) {
          let destinationPath = selectedEndpointItems.length
            ? `${endpointList.path}${selectedEndpointItems[0].name}/${file.path}`
            : `${endpointList.path}${file.path}`;

          transferItems.push({
            source_path: `${config.collection_base_path}/${file.path}`,
            destination_path: destinationPath,
            recursive: false,
          });
        }
      }
    } else {
      if (props.selectedJupyterItems.directories.length === 0 || props.selectedJupyterItems.directories.length > 1) {
        setLoading(false);
        setAPIError({ error: 'Please select one jupyter directory to transfer data to' });
      }

      // Loop through selectedEndpointItems from state
      for (let selectedEndpointItem of selectedEndpointItems) {
        transferItems.push({
          source_path: `${endpointList.path}${selectedEndpointItem.name}`,
          destination_path: `${config.collection_base_path}/${props.selectedJupyterItems.directories[0].path}/${selectedEndpointItem.name}`,
          recursive: selectedEndpointItem.type == 'dir' ? true : false,
        });
      }
    }

    let transferRequest = {
      source_endpoint: sourceEndpoint,
      destination_endpoint: destinationEndpoint,
      DATA: transferItems,
    };

    try {
      const transferResponse = await requestAPI<any>('submit_transfer', {
        body: JSON.stringify(transferRequest),
        method: 'POST',
      });
      setLoading(false);
      setTransfer(transferResponse);
    } catch (error) {
      setLoading(false);
      setAPIError({ error: error });
    }
  };

  if (apiError) {
    return (
      <>
        <button className='btn btn-sm btn-primary mb-4 mt-5' onClick={() => history.goBack()}>
          Back
        </button>
        <p className='fw-bold mt-3 text-danger'>Error: {apiError['error']}. Please try again.</p>
      </>
    );
  }

  if (loading) {
    return <h5 className='mt-5'>Loading</h5>;
  }

  return (
    <>
      {endpointList['DATA'].length > 0 ? (
        <div className='mt-5'>
          <h5>Browsing Collection {endpoint ? endpoint.display_name : endpointID}</h5>
          <button className='btn btn-sm btn-primary mb-4 mt-2' onClick={() => history.goBack()}>
            Back
          </button>

          {transfer && (
            <div className='alert alert-success alert-dismissible fade show'>
              <h4 className='alert-heading'>Accepted!</h4>
              <p>{transfer['message']}</p>
              <hr />
              <p className='mb-0'>
                <a
                  className='alert-link'
                  href={`https://app.globus.org/activity/${transfer['task_id']}`}
                  target='_blank'>
                  Check Status of Request <i className='fa-solid fa-arrow-up-right-from-square'></i>
                </a>
              </p>
            </div>
          )}
          <br />

          <div id='endpoint-list' className='border col-8 rounded py-3'>
            {endpointList['DATA'].map((listItem, index) => {
              return (
                <div className='form-check ms-3' key={index}>
                  {listItem['type'] == 'dir' ? (
                    <>
                      <input
                        onChange={handleEndpointItemSelect}
                        className='form-check-input'
                        type='checkbox'
                        value={JSON.stringify(listItem)}
                        data-list-item-name={listItem['name']}></input>
                      <label>
                        <Link to={`/endpoints/${endpointID}/items/${listItem['name']}`}>
                          <i className='fa-solid fa-folder-open'></i> {listItem['name']}
                        </Link>
                      </label>
                    </>
                  ) : (
                    <>
                      <input
                        onChange={handleEndpointItemSelect}
                        className='form-check-input'
                        type='checkbox'
                        value={JSON.stringify(listItem)}
                        data-list-item-name={listItem['name']}></input>
                      <label>
                        <i className='fa-solid fa-file'></i> {listItem['name']}
                      </label>
                    </>
                  )}
                </div>
              );
            })}
          </div>

          <div id='transfer-direction'>
            <div className='form-check form-check-inline mt-4'>
              <input
                className='form-check-input'
                onChange={handleTransferDirection}
                type='radio'
                name='transfer-direction'
                id='transfer-to-jupyter'
                value='transfer-to-jupyter'
              />
              <label className='form-check-label' htmlFor='transfer-to-jupyter'>
                Transfer to Jupyterlab
              </label>
            </div>
            <div className='form-check form-check-inline'>
              <input
                className='form-check-input'
                onChange={handleTransferDirection}
                type='radio'
                name='transfer-direction'
                id='transfer-from-jupyter'
                value='transfer-from-jupyter'
              />
              <label className='form-check-label' htmlFor='transfer-from-jupyter'>
                Transfer from Jupyterlab
              </label>
            </div>
            <div className='form-check form-check-inline pl-0'>
              <button className='btn btn-sm btn-primary' onClick={handleTransferRequest} type='button'>
                Submit Transfer Request
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <button className='btn btn-sm btn-primary mb-2 mt-3' onClick={() => history.goBack()}>
            Back
          </button>
          <p>No files or folders found</p>
        </div>
      )}
    </>
  );
};

export default Endpoint;
