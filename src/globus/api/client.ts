import {PromiseDelegate} from '@lumino/coreutils';
import {queryParams} from "../../utils";
import {GlobusResponse} from "./models";

const CLIENT_ID = '64d2d5b3-b77e-4e04-86d9-e3f143f563f7';
const REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code';

const GLOBUS_TOKEN_URL = 'https://auth.globus.org/v2/oauth2/token';

// TODO Symlink support
// TODO Share support
// TODO Create interface for errors
export const ERROR_CODES: any = {
    'ClientError.NotFound': 'Directory Not Found',
    'EndpointPermissionDenied': 'Endpoint Permission Denied',
    'ClientError.ActivationRequired': 'Endpoint Activation Required',
    'ExternalError.DirListingFailed.NotDirectory': 'Not a Directory',
    'ServiceUnavailable': 'Server Under Maintenance',
    'ExternalError.DirListingFailed.GCDisconnected': 'Globus Connect Not Running',
    'ExternalError.DirListingFailed': 'Directory Listing Failed',
    'ExternalError.DirListingFailed.PermissionDenied': 'Permission Denied',
    'ExternalError.DirListingFailed.ConnectFailed': 'Connection Failed'
};

export let globusAuthorized = new PromiseDelegate<void>();

/**
 * Initializes the Globus client
 * @param {any} data 
 */
export function initializeGlobusClient(data: any) {
    Private.tokens.data = data;
}

/**
 * Gets the access tokens by using the provided authorization code
 * @param {string} authCode 
 * @param {string} verifier 
 * @returns {Promise}
 */
export async function getTokens(authCode: string, verifier: any): Promise<any> {
    // Globus's OAuth 2.0 endpoint for requesting an access token
    let oauth2Endpoint = GLOBUS_TOKEN_URL;

    // Create <form> element to submit parameters to OAuth 2.0 endpoint.
    let form: HTMLFormElement = document.createElement('form');
    form.method = 'GET'; // Send as a GET request.
    form.action = oauth2Endpoint;
    form.target = window.location.href;

    return new Promise<GlobusResponse>((resolve, reject) => {
        exchangeOAuth2Token(authCode, verifier.toString())
            .then(data => {
                globusAuthorized.resolve(data);
                resolve(data);
            })
            .catch(e => {
                console.log(e);
                reject();
            });
    });

}

/**
 * Exchanges a 0Auth2Token for Globus access tokens
 * @param {string} token
 * @param {string} verifier
 */
export async function exchangeOAuth2Token(token: string, verifier: string) {
    // Globus's OAuth 2.0 endpoint for requesting an access token
    let oauth2Endpoint = GLOBUS_TOKEN_URL;

    // Parameters to pass to OAuth 2.0 endpoint.
    let params: any = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
        'code': token,
        'code_verifier': verifier
    };

    let formData = queryParams(params);

    let fetchAccessToken: Promise<any> = new Promise<any>((resolve, reject) =>
        fetch(oauth2Endpoint, {
            method: 'POST',
            body: formData,
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            }
        }).then(function(response) {
            if (response.status >= 400) {
                reject(response.statusText);
            }
            return response.json();
        }).then(function(data) {
            resolve(data);
        })
    );

    // Wait for fetch to be done and then return token(s)
    return await fetchAccessToken;
}

/**
 * Invalidates the globusAuthorized promise and sets up a new one.
 */
export function signOut() {
    sessionStorage.removeItem('data');
    globusAuthorized = new PromiseDelegate<void>();
}

/**
 * Makes a basic Globus Request and returns the response as a json
 * @param {string} url
 * @param options
 * @returns {Promise<GlobusResponse>}
 */
export function makeGlobusRequest(url: string, options: any): Promise<GlobusResponse> {
    return new Promise<GlobusResponse>((resolve, reject) => {
        fetch(url, options).then(async response => {
            if (response.status >= 400) {
                reject(await response.json());
            }
            else {
                resolve(await response.json());
            }
        });
    })
}

/**
 * Contains the tokens required by the extension.
 */
export namespace Private {
    export let tokens = new class {
        _data: any;
        searchToken: string;
        transferToken: string;

        set data(data: any) {
            this._data = data;
            this.searchToken = data.other_tokens[0].access_token;
            this.transferToken = data.other_tokens[1].access_token;
        }
    };
}
