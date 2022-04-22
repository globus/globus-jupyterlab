import { Link } from 'react-router-dom';
import React, { useEffect, useState } from 'react';
import { useHistory, useParams } from 'react-router-dom';
import { useRecoilValue } from 'recoil';
import { requestAPI } from '../handler';

import { ConfigAtom } from './GlobusObjects';

const Endpoint = (props) => {
  // Local State
  const [apiError, setAPIError] = useState(null);
  const [endpointList, setEndpointList] = useState({ DATA: [] });
  const [endpoint, setEndpoint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedEndpointItems, setSelectedEndpointItems] = useState([]);
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
    setEndpointList({ DATA: [] });
    setLoading(true);
    try {
      let url = `/globus-jupyterlab/operation_ls?endpoint=${endpointID}`;
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
    var transferItems = [];

    var sourceEndpoint = transferDirection == 'transfer-to-endpoint' ? config.collection_id : endpoint.id;
    var destinationEndpoint = transferDirection == 'transfer-to-endpoint' ? endpoint.id : config.collection_id;

    console.log(props);
    if (transferDirection == 'transfer-to-endpoint') {
      // Loop through selectedJupyterItems from props
      if (props.selectedJupyterItems.directories.length) {
        for (let directory of props.selectedJupyterItems.directories) {
          transferItems.push({
            source_path: `${config.collection_base_path}/${directory.path}`,
            destination_path: directory.path,
            recursive: true
          });
        };
      }

      if (props.selectedJupyterItems.files.length) {
        for (let file of props.selectedJupyterItems.files) {
          transferItems.push({
            source_path: `${config.collection_base_path}/${file.path}`,
            destination_path: file.path,
            recursive: false
          });
        }
      }
    } else {
      // Loop through selectedEndpointItems from state
      for (let selectedEndpointItem of selectedEndpointItems) {
        transferItems.push({
          source_path: selectedEndpointItem.name,
          destination_path: `${config.collection_base_path}/${selectedEndpointItem.name}`,
          recursive: selectedEndpointItem.type == 'dir' ? true : false,
        });
      };
    }

    let transferRequest = {
      source_endpoint: sourceEndpoint,
      destination_endpoint: destinationEndpoint,
      DATA: transferItems,
    };
    console.log(transferRequest)
    try {
      const reply = await requestAPI<any>('submit_transfer', {
        body: JSON.stringify(transferRequest),
        method: 'POST',
      });
      console.log(reply);
    } catch (reason) {
      console.error(
        `Error on POST /globus-jupyterlab/submit_transfer ${transferRequest}.\n${reason}`
      );
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
          <br />

          {endpointList['DATA'].map((listItem) => {
            return (
              <div className='form-check'>
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

          {selectedEndpointItems.length > 0 && (
            <>
              <div className='form-check form-check-inline mt-4'>
                <input
                  className='form-check-input'
                  onChange={handleTransferDirection}
                  type='radio'
                  name='transfer-direction'
                  id='transfer-to-endpoint'
                  value='transfer-to-endpoint'
                />
                <label className='form-check-label' htmlFor='transfer-to-endpoint'>
                  Transfer to Collection
                </label>
              </div>
              <div className='form-check form-check-inline'>
                <input
                  className='form-check-input'
                  onChange={handleTransferDirection}
                  type='radio'
                  name='transfer-direction'
                  id='transfer-from-endpoint'
                  value='transfer-from-endpoint'
                />
                <label className='form-check-label' htmlFor='transfer-from-endpoint'>
                  Transfer from Collection
                </label>
              </div>
              <div className='form-check form-check-inline pl-0'>
                <button className='btn btn-sm btn-primary' onClick={handleTransferRequest} type='button'>
                  Submit Transfer Request
                </button>
              </div>
            </>
          )}
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
