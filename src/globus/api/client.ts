import {PromiseDelegate} from '@phosphor/coreutils';
import {queryParams} from "../../utils";
import {GlobusResponse} from "./models";

// const CLIENT_ID = '7c9085aa-3bcf-4a5b-a7b8-77e41daa4d1a';
// const REDIRECT_URI = 'https://hub.mybinder.org/hub/login';
// const CLIENT_ID = 'a53a92fb-c4e0-4aa6-9e12-bbf939180305';
// const REDIRECT_URI = window.location.href;
const CLIENT_ID = 'e54de045-d346-42ef-9fbc-5d466f4a00c6';
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

export function initializeGlobusClient(data: any) {
    Private.tokens.data = data;
}

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
                resolve();
            })
            .catch(e => {
                console.log(e);
                reject();
            });
    });

}

/**
 * Exchanges a 0Auth2Token for Globus access tokens
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

    // Wait for fetch to be done and then return
    return await fetchAccessToken;
}

export function signOut() {
    // Invalidate the globusAuthorized promise and set up a new one.
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
