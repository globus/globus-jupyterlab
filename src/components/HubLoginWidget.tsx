import React, { useState } from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { requestAPI } from '../handler';

const HubLogin = (props) => {
  const [apiError, setAPIError] = useState(null);
  const [hubInputCode, setHubInputCode] = useState(null);

  const handleHubInputChange = (event) => {
    setHubInputCode(event.target.value);
  };

  const handleHubLogin = async (event) => {
    event.preventDefault();

    try {
      let response = await requestAPI<any>(`oauth_callback_manual?code=${hubInputCode}`);
      console.log(response);
    } catch (error) {
      setAPIError(error);
    }
  };

  return (
    <div className='container mt-5'>
      <div className='row'>
        <div className='col-8'>

          {apiError && (
            <div id='api-error' className='alert alert-danger'>
              <strong>
                Error {apiError.response.status}: {apiError.response.statusText}.
              </strong>{' '}
              Please try again.
            </div>
          )}
          
          <label htmlFor='code-input' className='form-label'>
            Paste Code and Click Login
          </label>
          <input
            type='text'
            id='code-input'
            className='form-control mb-3'
            name='code-input'
            onChange={handleHubInputChange}></input>
          <button type='button' className='btn btn-primary' onClick={handleHubLogin}>
            Login
          </button>
        </div>
      </div>
    </div>
  );
};

export class HubLoginWidget extends ReactWidget {
  render(): JSX.Element {
    return <HubLogin />;
  }
}
