import React, { useEffect, useRef, useState } from "react";
import { ReactWidget } from "@jupyterlab/apputils";

import { requestAPI } from "../handler";

export const HubLogin = (props) => {
  const [apiError, setAPIError] = useState(null);
  const [hubInputCode, setHubInputCode] = useState(null);

  const hubLoginButton = useRef();

  useEffect(() => {
    // @ts-ignore
    hubLoginButton.current.disabled = true;
  }, []);

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
      await requestAPI<any>(`oauth_callback_manual?code=${hubInputCode}`);
    } catch (error) {
      setAPIError(error);
    }
  };

  if (apiError) {
    return (
      <div className="alert alert-danger alert-dismissible col-8 fade show">
        <strong>
          Error {apiError.response.status}: {apiError.response.statusText}.
        </strong>{" "}
        {apiError.details && apiError.details}
        <button
          type="button"
          className="btn-close"
          data-bs-dismiss="alert"
          aria-label="Close"
        ></button>
      </div>
    );
  }

  return (
    <div className="container mt-3">
      <div className="row">
        <div className="col-8">
          {apiError && (
            <div id="api-error" className="alert alert-danger">
              <strong>
                Error {apiError.response.status}: {apiError.response.statusText}
                .
              </strong>{" "}
              Please try again.
            </div>
          )}

          <ol className="list-group">
            <li className="list-group-item d-flex justify-content-between align-items-start">
              <div className="ms-2 me-auto">
                <div className="fw-bold mb-3">
                  1. Log In to Globus to obtain an Authorization Code for this
                  transfer
                </div>
                <button
                  type="button"
                  className="btn btn-outline-primary"
                  onClick={() => {
                    let loginURL =
                      "loginURL" in props
                        ? props.loginURL
                        : "globus-jupyterlab/login";
                    window
                      .open(
                        loginURL,
                        "Login with Globus",
                        "height=600,width=800"
                      )
                      .focus();
                  }}
                >
                  Log In to Globus
                </button>
              </div>
            </li>

            <li className="list-group-item">
              <div className="ms-2 me-auto">
                <div className="fw-bold mb-3">
                  2. Copy and paste the Authorization Code you just received
                  from Globus
                </div>
                <label htmlFor="code-input" className="form-label">
                  Authorization Code
                </label>
                <input
                  type="text"
                  id="code-input"
                  className="form-control mb-3"
                  name="code-input"
                  onChange={handleHubInputChange}
                ></input>
                <button
                  type="button"
                  className="btn btn-primary"
                  ref={hubLoginButton}
                  onClick={handleHubLogin}
                >
                  Continue
                </button>
              </div>
            </li>
          </ol>
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
