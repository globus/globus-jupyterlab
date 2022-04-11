import React, { useState } from 'react';
import { Route, useHistory } from 'react-router-dom';

import Endpoint from './Endpoint';
import Endpoints from './Endpoints';

const EndpointSearch = (props) => {
  const [apiError, setAPIError] = useState(null);
  const [endpoints, setEndpoints] = useState({ DATA: [] });
  const [endpointValue, setEndpointValue] = useState('');
  const [loading, setLoading] = useState(false);

  const history = useHistory();

  // Event Handlers
  const handleEndpointValueChange = (event) => {
    setEndpointValue(event.target.value);
  };

  const handleSearchEndpointClick = async (event) => {
    setAPIError(null);
    setEndpoints({ DATA: [] });
    setLoading(true);
    try {
      let response = await fetch(`/globus-jupyterlab/endpoint_search?filter_fulltext=${endpointValue}`, {
        headers: {
          Allow: 'application/json',
          'Content-Type': 'application/json',
        },
      });
      let endpoints = await response.json();
      if ('error' in endpoints) {
        throw endpoints;
      }
      setEndpoints(endpoints);
      setLoading(false);
      history.push('/endpoints');
    } catch (error: any) {
      setLoading(false);
      setAPIError(error);
    }
  };

  if (apiError) {
    return <p className='fw-bold text-danger'>Error: {apiError['error']}. Please try again.</p>;
  }

  if (loading) {
    return <h5>Loading</h5>;
  }

  return (
    <div id='endpoint-search' className='mb-4'>
      <h5>Search Collections for Transferring</h5>

      <div className='row'>
        <div className='col-8'>
          <input
            id='endpoint-input'
            className='form-control'
            type='text'
            value={endpointValue}
            onChange={handleEndpointValueChange}
          />
        </div>
        <div className='col'>
          <button className='btn btn-primary' onClick={handleSearchEndpointClick}>
            Search Collections
          </button>
        </div>
      </div>

      <Route
        exact
        path='/endpoints'
        render={(props) => {
          return <Endpoints {...props} endpoints={endpoints} />;
        }}
      />
      <Route exact path='/endpoints/:endpointID'>
        <Endpoint selectedJupyterItems={props.selectedJupyterItems} />
      </Route>
      <Route path='/endpoints/:endpointID/items/:path'>
        <Endpoint selectedJupyterItems={props.selectedJupyterItems} />
      </Route>
    </div>
  );
};

export default EndpointSearch;
