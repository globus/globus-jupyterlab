import React, { useRef, useState } from 'react';
import { requestAPI } from '../handler';
import { Route, useHistory } from 'react-router-dom';

import Endpoint from './Endpoint';
import Endpoints from './Endpoints';

const EndpointSearch = (props) => {
  const [apiError, setAPIError] = useState(null);
  const [endpoints, setEndpoints] = useState({ DATA: [] });
  const [endpointValue, setEndpointValue] = useState('');
  const [loading, setLoading] = useState(false);

  const endpointSearch = useRef();
  const history = useHistory();

  const handleEndpointClick = (event) => {
    // @ts-ignore
    endpointSearch.current.style.display = 'none';
  };

  const handleEndpointValueChange = (event) => {
    setEndpointValue(event.target.value);
  };

  const handleSearchEndpoints = async (event) => {
    let keyCode = event.keyCode;
    if (keyCode == 13) {
      setAPIError(null);
      setEndpoints({ DATA: [] });
      setLoading(true);
      try {
        let endpoints = await requestAPI<any>(`endpoint_search?filter_fulltext=${endpointValue}`);
        setEndpoints(endpoints);
        setLoading(false);
        history.push('/endpoints');
      } catch (error: any) {
        setLoading(false);
        setAPIError(error);
      }
    }
  };

  const handleShowSearch = () => {
    // @ts-ignore
    endpointSearch.current.style.display = 'block';
  }

  if (apiError) {
    return (
      <div id='api-row' className='row'>
        <div className='col-8'>
          <div className='alert alert-danger'>
            <strong>
              Error {apiError.response.status}: {apiError.response.statusText}.
            </strong>{' '}
            Please try again.
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return <h5>Loading</h5>;
  }

  return (
    <div id='endpoint-search' className='mb-4'>
      <div ref={endpointSearch}>
        <h5>Search for Globus Collections</h5>

        <div className='row'>
          <div className='col-8'>
            <input
              id='endpoint-input'
              className='form-control'
              placeholder='Start typing and press enter to search'
              type='text'
              value={endpointValue}
              onChange={handleEndpointValueChange}
              onKeyDown={handleSearchEndpoints}
            />
          </div>
        </div>
      </div>

      <Route
        exact
        path='/endpoints'
        render={(props) => {
          return <Endpoints {...props} endpoints={endpoints} handleEndpointClick={handleEndpointClick} />;
        }}
      />
      <Route exact path='/endpoints/:endpointID'>
        <Endpoint {...props} selectedJupyterItems={props.selectedJupyterItems} handleShowSearch={handleShowSearch} />
      </Route>
      <Route path='/endpoints/:endpointID/items/:path'>
        <Endpoint {...props} selectedJupyterItems={props.selectedJupyterItems} handleShowSearch={handleShowSearch} />
      </Route>
    </div>
  );
};

export default EndpointSearch;
