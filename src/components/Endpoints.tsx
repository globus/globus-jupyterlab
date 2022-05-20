import { Link } from 'react-router-dom';

import React from 'react';

const Endpoints = (props) => {
  return (
    <div className='row'>
      {props.endpoints['DATA'].length > 0 && (
        <div className='col-8'>
          <div className='list-group'>
            {props.endpoints['DATA'].map((endpoint) => {
              return (
                <Link
                  key={endpoint.id}
                  to={`/endpoints/${endpoint.id}`}
                  className='list-group-item list-group-item-action flex-column align-items-start'
                  onClick={props.handleEndpointClick}>
                  <h5 className='mb-1'>
                    <i className='fa-solid fa-layer-group'></i>&nbsp;
                    {endpoint.display_name}
                  </h5>

                  <p className='mb-0 mt-2 fw-bold'>Owner:</p>
                  <p className='mb-1'>{endpoint.owner_string}</p>

                  {endpoint.description && (
                    <>
                      <p className='mb-0 mt-2 fw-bold'>Description:</p>
                      <p className='mb-1'>{endpoint.description}</p>
                    </>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
 export default Endpoints;