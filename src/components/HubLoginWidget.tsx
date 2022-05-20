import React, { useEffect, useRef, useState } from 'react';
import { ReactWidget } from '@jupyterlab/apputils';

import { getBaseURL } from '../utilities';
import { requestAPI } from '../handler';

const HubLogin = (props) => {
  const [apiError, setAPIError] = useState(null);
  const [hubInputCode, setHubInputCode] = useState(null);

  const hubLoginButton = useRef();

  useEffect(() => {
    // @ts-ignore
    hubLoginButton.current.disabled = true;
  }, [])

  const handleHubInputChange = (event) => {
    if (event.target.value) {
      // @ts-ignore
      hubLoginButton.current.disabled = false;
    }
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
    <div className='container mt-3'>
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
            Paste Native App Authorization Code and Click Complete Login.
            <br />
            To start another Globus auth flow, click Login to Globus.
          </label>
          <input
            type='text'
            id='code-input'
            className='form-control mb-3'
            name='code-input'
            onChange={handleHubInputChange}></input>
          <div className='btn-group'>
            <button type='button' className='btn btn-primary' ref={hubLoginButton} onClick={handleHubLogin}>
              Complete Login
            </button>
            <button
              type='button'
              className='btn btn-outline-primary'
              onClick={() =>
                window.open(getBaseURL('globus-jupyterlab/login'), 'Login with Globus', 'height=600,width=800').focus()
              }>
              Login to Globus
            </button>
          </div>
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
