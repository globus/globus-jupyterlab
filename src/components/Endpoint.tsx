import { Link, useLocation } from "react-router-dom";
import React, { useEffect, useState } from "react";
import { requestAPI } from "../handler";
import { useHistory, useParams } from "react-router-dom";
import { useRecoilValue } from "recoil";

import { ConfigAtom } from "./GlobusObjects";
import { HubLogin } from "./HubLoginWidget";

import * as path from "path";
var _path = path;

const useQuery = () => {
  const { search } = useLocation();
  return React.useMemo(() => new URLSearchParams(search), [search]);
};

const Endpoint = (props) => {
  // Local State
  const [apiError, setAPIError] = useState(null);
  const [endpointList, setEndpointList] = useState({ DATA: [], path: null });
  const [endpoint, setEndpoint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loginURL, setLoginURL] = useState(null);
  const [selectedEndpointItems, setSelectedEndpointItems] = useState([]);
  const [transfer, setTransfer] = useState(null);

  const itemsRef = React.useRef([]);
  const [lastChecked, setLastChecked] = useState(null);
  const [shift, setShift] = useState(false);

  // Recoil (global) State
  const config = useRecoilValue(ConfigAtom);

  // React Router history and params
  let history = useHistory();
  let params: any = useParams();
  let endpointID = params.endpointID;
  let path = params.path;
  let query = useQuery();

  // ComponentDidMount Functions
  useEffect(() => {
    const handleKeyUp = (event) => {
      if (event.key === "Shift") {
        setShift(false);
      }
    };
    document.addEventListener("keyup", handleKeyUp);
    return () => {
      document.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.shiftKey || event.metaKey) {
        setShift(true);
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  useEffect(() => {
    listEndpointItems(endpointID, path);
    return () => {
      setAPIError(null);
      setEndpointList({ DATA: [], path: null });
    };
  }, [endpointID, path]);

  // @ts-ignore
  const getSelectedFiles = () => {
    const selectedFiles = props.factory.tracker.currentWidget.selectedItems();
    let jupyterItems = [],
      fileCheck = true;

    while (fileCheck) {
      let file = selectedFiles.next();
      if (file) {
        jupyterItems.push(file);
      } else {
        fileCheck = false;
      }
    }

    return jupyterItems;
  };

  const listEndpointItems = async (endpointID, path = null) => {
    setLoading(true);
    setAPIError(null);
    setEndpointList({ DATA: [], path: null });

    let endpoint = await requestAPI(`endpoint_detail?endpoint=${endpointID}`);
    if (!endpoint["activated"] && endpoint["expires_in"] == 0) {
      let activated = await requestAPI<any>("endpoint_autoactivate", {
        body: JSON.stringify({ endpoint_id: endpoint["id"] }),
        method: "POST",
      });
      // Need to research if there is anything meaningful to do with the activation result
      console.log(activated);
    }
    setEndpoint(endpoint);

    try {
      var fullPath = query.get("full-path");
      var url = `operation_ls?endpoint=${endpointID}`;
      if (fullPath) {
        url = `${url}&path=${fullPath}`;
      }
      const listItems = await requestAPI<any>(url);
      setLoading(false);
      setEndpointList(listItems);
    } catch (error) {
      setLoading(false);
      setAPIError({ ...error, ...{ global: true } });

      let error_response = await error.response.json();

      /*
        Note: This probably isn't a great UX to simply pop up a login page, but it
        does demonstrate the base functionality for picking endpoints
      */
      if ("login_url" in error_response) {
        // Poll for successful authentication.
        var lastConfig = await requestAPI<any>("config");
        var lastLogin = new Date(lastConfig.last_login).getTime();

        let authInterval = window.setInterval(async () => {
          const updatedConfig = await requestAPI<any>("config");
          var newLogin = new Date(updatedConfig.last_login).getTime();

          if (newLogin !== lastLogin) {
            history.push("/");
            history.replace(`/endpoints/${endpointID}`);
            clearInterval(authInterval);
          }
        }, 1000);

        if (config.is_hub) {
          setAPIError(null);
          setLoginURL(error_response.login_url);
        } else {
          window
            .open(
              error_response.login_url,
              "Globus Login",
              "height=600,width=800"
            )
            .focus();
        }
      }
    }

    setLoading(false);
  };

  // Event Handlers
  const handleEndpointSelect = (event) => {
    var checked;
    if (shift) {
      if (lastChecked !== null) {
        let checkboxes = itemsRef.current;

        let start = checkboxes.indexOf(lastChecked);
        let end = checkboxes.indexOf(event.target);
        checked = checkboxes.slice(
          Math.min(start, end),
          Math.max(start, end) + 1
        );

        checked.forEach((el) => {
          el.checked = start < end ? true : false;
        });
      }
    } else {
      checked = [event.target];
    }

    // Only need unique values from checked
    checked = [...new Set(checked)];

    // Reset selectedEndpointItems if checked items length > 1
    if (checked.length > 1) {
      setSelectedEndpointItems([]);
    }

    // Build selectedEndpointItems
    checked.forEach((el: HTMLInputElement, index: Number) => {
      if (el.checked) {
        setSelectedEndpointItems((selectedEndpointItems) => {
          return [JSON.parse(el.value), ...selectedEndpointItems];
        });
      } else {
        const removeItem = JSON.parse(el.value);
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
    });

    setLastChecked(event.target);
  };

  const handleTransferToJupyter = async (event) => {
    event.preventDefault();
    setAPIError(null);
    setLoading(true);
    setTransfer(null);

    var destinationEndpoint = config.collection_id;
    var sourceEndpoint = endpoint.id;
    var transferItems = [];

    if (
      props.selectedJupyterItems.directories.length === 0 ||
      props.selectedJupyterItems.directories.length > 1
    ) {
      setLoading(false);
      setAPIError({
        response: {
          status: "DirectorySelectionError",
          statusText:
            "To transfer to Jupyter Hub, you must select only one directory to transfer to.",
        },
      });
    } else {
      // Loop through selectedEndpointItems from state
      for (let selectedEndpointItem of selectedEndpointItems) {
        let sourcePath = _path.posix.resolve(
          endpointList.path,
          selectedEndpointItem.name
        );
        let destinationPath = _path.posix.resolve(
          config.collection_base_path,
          props.selectedJupyterItems.directories[0].path,
          selectedEndpointItem.name
        );

        transferItems.push({
          source_path: sourcePath,
          destination_path: destinationPath,
          recursive: selectedEndpointItem.type == "dir" ? true : false,
        });
      }

      let transferRequest = {
        source_endpoint: sourceEndpoint,
        destination_endpoint: destinationEndpoint,
        DATA: transferItems,
      };

      try {
        const transferResponse = await requestAPI<any>("submit_transfer", {
          body: JSON.stringify(transferRequest),
          method: "POST",
        });
        setLoading(false);
        setTransfer(transferResponse);
      } catch (error) {
        setLoading(false);
        setAPIError(error);
      }
    }
  };

  const handleTransferFromJupyter = async (event) => {
    event.preventDefault();
    setAPIError(null);
    setLoading(true);
    setTransfer(null);

    var destinationEndpoint = endpoint.id;
    var sourceEndpoint = config.collection_id;
    var transferItems = [];

    if (selectedEndpointItems.length > 1) {
      setAPIError({
        response: {
          status: "DirectorySelectionError",
          statusText:
            "Please only select one remote directory to transfer data to",
        },
      });
    }

    // Loop through selectedJupyterItems from props
    if (props.selectedJupyterItems.directories.length) {
      for (let directory of props.selectedJupyterItems.directories) {
        let destinationPath = selectedEndpointItems.length
          ? _path.posix.resolve(
              endpointList.path,
              selectedEndpointItems[0].name,
              directory.path
            )
          : _path.posix.resolve(endpointList.path, directory.path);

        let sourcePath = _path.posix.resolve(
          config.collection_base_path,
          directory.path
        );

        transferItems.push({
          source_path: sourcePath,
          destination_path: destinationPath,
          recursive: true,
        });
      }
    }

    if (props.selectedJupyterItems.files.length) {
      for (let file of props.selectedJupyterItems.files) {
        let destinationPath = selectedEndpointItems.length
          ? _path.posix.resolve(
              endpointList.path,
              selectedEndpointItems[0].name,
              file.path
            )
          : _path.posix.resolve(endpointList.path, file.path);

        let sourcePath = _path.posix.resolve(
          config.collection_base_path,
          file.path
        );

        transferItems.push({
          source_path: sourcePath,
          destination_path: destinationPath,
          recursive: false,
        });
      }
    }

    let transferRequest = {
      source_endpoint: sourceEndpoint,
      destination_endpoint: destinationEndpoint,
      DATA: transferItems,
    };

    try {
      const transferResponse = await requestAPI<any>("submit_transfer", {
        body: JSON.stringify(transferRequest),
        method: "POST",
      });
      setLoading(false);
      setTransfer(transferResponse);
    } catch (error) {
      setLoading(false);
      setAPIError(error);
    }
  };

  if (apiError && apiError.global) {
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

  if (loading) {
    return <h5 className="mt-3">Loading</h5>;
  }

  if (loginURL) {
    return <HubLogin loginURL={loginURL} />;
  }

  return (
    <>
      {endpointList["DATA"].length > 0 ? (
        <div className="mt-3">
          <h5>
            Browsing Collection {endpoint ? endpoint.display_name : endpointID}
          </h5>
          <div className="btn-group mb-4 mt-2">
            <button
              className="btn btn-sm btn-outline-primary"
              onClick={() => history.goBack()}
            >
              <i className="fa-solid fa-turn-up"></i> Up one folder
            </button>
            <button
              className="btn btn-sm btn-outline-primary"
              onClick={props.handleShowSearch}
            >
              <i className="fa-solid fa-magnifying-glass"></i> Show search
            </button>
          </div>

          {transfer && (
            <div className="alert alert-success alert-dismissible col-8 fade show">
              <h4 className="alert-heading">Accepted!</h4>
              <p>{transfer["message"]}</p>
              <hr />
              <p className="mb-0">
                <a
                  className="alert-link"
                  href={`https://app.globus.org/activity/${transfer["task_id"]}`}
                  target="_blank"
                >
                  Check Status of Request{" "}
                  <i className="fa-solid fa-arrow-up-right-from-square"></i>
                </a>
              </p>
              <button
                type="button"
                className="btn-close"
                data-bs-dismiss="alert"
                aria-label="Close"
              ></button>
            </div>
          )}

          {apiError && (
            <div className="alert alert-danger alert-dismissible col-8 fade show">
              <strong>
                Error {apiError.response.status}: {apiError.response.statusText}
                .
              </strong>{" "}
              {apiError.details && apiError.details}
              <button
                type="button"
                className="btn-close"
                data-bs-dismiss="alert"
                aria-label="Close"
              ></button>
            </div>
          )}
          <br />

          <div id="endpoint-list" className="border col-8 rounded py-3">
            {endpointList["DATA"].map((listItem, index) => {
              return (
                <div className="form-check ms-3" key={index}>
                  {listItem["type"] == "dir" ? (
                    <>
                      <input
                        className="form-check-input"
                        type="checkbox"
                        value={JSON.stringify(listItem)}
                        ref={(el) => (itemsRef.current[index] = el)}
                        onChange={handleEndpointSelect}
                        data-list-item-name={listItem["name"]}
                      ></input>
                      <label>
                        <Link
                          to={`/endpoints/${endpointID}/items/${listItem["name"]}?full-path=${endpointList["path"]}${listItem["name"]}`}
                        >
                          <i className="fa-solid fa-folder-open"></i>{" "}
                          {listItem["name"]}
                        </Link>
                      </label>
                    </>
                  ) : (
                    <>
                      <input
                        className="form-check-input"
                        type="checkbox"
                        value={JSON.stringify(listItem)}
                        ref={(el) => (itemsRef.current[index] = el)}
                        onChange={handleEndpointSelect}
                        data-list-item-name={listItem["name"]}
                      ></input>
                      <label>
                        <i className="fa-solid fa-file"></i> {listItem["name"]}
                      </label>
                    </>
                  )}
                </div>
              );
            })}
          </div>

          <div id="transfer-direction">
            <div className="btn-group mt-4">
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                onClick={handleTransferToJupyter}
              >
                <i className="fa-solid fa-arrow-left"></i> Transfer To
                JupyterLab
              </button>
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                onClick={handleTransferFromJupyter}
              >
                <i className="fa-solid fa-arrow-right"></i> Transfer From
                JupyterLab
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <button
            className="btn btn-sm btn-primary mb-2 mt-3"
            onClick={() => history.goBack()}
          >
            Back
          </button>
          <p>No files or folders found</p>
        </div>
      )}
    </>
  );
};

export default Endpoint;
