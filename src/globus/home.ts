import {Widget, PanelLayout} from '@lumino/widgets';
import CryptoJS = require('crypto-js');
import {getTokens, globusAuthorized, initializeGlobusClient} from "./api/client";
import {GlobusWidgetManager} from "./widget_manager";
import {queryParams, GLOBUS_BUTTON, GLOBUS_INPUT, GLOBUS_BORDER} from "../utils";

/**
 * CSS classes
 */
const GLOBUS_HOME = 'jp-Globus-home';
const GLOBUS_TAB_LOGO = 'jp-Globus-tablogo';
const GLOBUS_LOGIN_SCREEN = 'jp-Globus-loginScreen';
const GLOBUS_LOGO = 'jp-Globus-logo';

const CLIENT_ID = '64d2d5b3-b77e-4e04-86d9-e3f143f563f7';
const REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code';
const SCOPES = 'openid email profile urn:globus:auth:scope:transfer.api.globus.org:all urn:globus:auth:scope:search.api.globus.org:all';

export const SIGN_OUT = 'globus-signOut';

/**
 * Widget for hosting the Globus Home.
 */
export class GlobusHome extends Widget {
    readonly globusLogin: GlobusLogin;
    readonly widgetManager: GlobusWidgetManager;

    constructor(widgetManager: GlobusWidgetManager) {
        super();

        this.id = 'globus-home';
        this.addClass(GLOBUS_HOME);

        this.layout = new PanelLayout();
        this.globusLogin = new GlobusLogin();
        this.widgetManager = widgetManager;

        this.title.iconClass = GLOBUS_TAB_LOGO;
        this.title.closable = true;

        this.showLoginScreen();
        this.globusLogin.attemptSignIn();
    }

    /**
     * Displays login screen and waits for authorization
     */
    public showLoginScreen() {
        (this.layout as PanelLayout).addWidget(this.globusLogin);

        // After globus authorization, show the widget manager.
        globusAuthorized.promise.then((data: any) => {
            // Store login data in the session
            sessionStorage.setItem('data', JSON.stringify(data));
            initializeGlobusClient(data);

            // Hide login screen
            this.globusLogin.parent = null;

            // Initialize widgetManager and add it to layout
            this.widgetManager.update();
            (this.layout as PanelLayout).addWidget(this.widgetManager);
        });
    }
}

/**
 * Widget for hosting the Globus Login.
 */
export class GlobusLogin extends Widget {

    verifier: any;

    constructor() {
        super();
        this.addClass(GLOBUS_LOGIN_SCREEN);

        // Create the logo
        const logo = document.createElement('div');
        logo.className = GLOBUS_LOGO;
        
        // Create the text for explaining the auth code
        let authText = document.createElement('p');
        authText.textContent = 'Please use the new tab to get an authorization code and paste it in the box below';
        authText.style.textAlign = 'center';
        authText.style.display = 'none';
        
        // Create the login button (<a> HTML tag with button appearance).
        let signInButton = document.createElement('a');
        signInButton.setAttribute('href', this.getAuthUrl());
        signInButton.setAttribute('target', '_blank');
        signInButton.setAttribute('appearance', 'button');
        signInButton.title = 'Log into your Globus account';
        signInButton.textContent = 'SIGN IN';
        signInButton.className = `${GLOBUS_BUTTON}`;
        
        // Create the auth-code input and submit button
        let authCodeInput: HTMLInputElement = document.createElement('input');
        authCodeInput.type = 'text';
        authCodeInput.className = `${GLOBUS_INPUT} ${GLOBUS_BORDER}`;
        authCodeInput.placeholder = 'Paste your auth code here';
        authCodeInput.style.display = 'none';
        
        let submitAuthCodeButton = document.createElement('button');
        submitAuthCodeButton.textContent = 'SUBMIT TOKEN';
        submitAuthCodeButton.className = `${GLOBUS_BUTTON}`;
        submitAuthCodeButton.style.display = 'none';
        
        // Create the cancel button (returns user to main login)
        let cancelButton = document.createElement('button');
        cancelButton.textContent = 'CANCEL';
        cancelButton.className = `${GLOBUS_BUTTON}`; 
        cancelButton.style.background = '#340d0d';
        cancelButton.style.display = 'none';

        // Create error message to display if login fails
        let errorMessage = document.createElement('p');
        errorMessage.textContent = 'An error occurred, please try again or click the Cancel button to get a new authorization code.';
        errorMessage.style.color = 'red';
        errorMessage.style.textAlign = 'center';
        errorMessage.style.display = 'none';

        // Add Event Listeners
        signInButton.addEventListener('click', () => {
            signInButton.style.display = 'none';
            authText.style.display = 'block';
            authCodeInput.style.display = 'block';
            submitAuthCodeButton.style.display = 'block';
            cancelButton.style.display = 'block';
        });
        submitAuthCodeButton.addEventListener('click', () => {
            getTokens(authCodeInput.value, this.verifier)
                .then(data => {
                    signInButton.style.display = 'block';
                    authText.style.display = 'none';
                    authCodeInput.style.display = 'none';
                    submitAuthCodeButton.style.display = 'none';
                    cancelButton.style.display = 'none';
                    errorMessage.style.display = 'none';
                })
                .catch(e => {
                    errorMessage.style.display = 'block';
                });
        
        });
        cancelButton.addEventListener('click', () => {
            signInButton.style.display = 'block';
            authText.style.display = 'none';
            authCodeInput.style.display = 'none';
            submitAuthCodeButton.style.display = 'none';
            cancelButton.style.display = 'none';
            errorMessage.style.display = 'none';
        });
        
        // Add the elements
        this.node.appendChild(logo);
        this.node.appendChild(authText);
        this.node.appendChild(signInButton);
        this.node.appendChild(authCodeInput);
        this.node.appendChild(submitAuthCodeButton);
        this.node.appendChild(cancelButton);
        this.node.appendChild(errorMessage);
        
    }

    /**
     * Generates the Auth URL and returns it (as a string). 
     */
    private getAuthUrl(): string {
        // Define the basic auth URL
        let authUrl = 'https://auth.globus.org/v2/oauth2/authorize?';

        // Generates verifier and challenge to follow 0Auth2 protocol
        this.generateVerifier();
        let challenge = this.generateCodeChallenge(this.verifier);

        // Authorization Request parameters
        let params: any = {
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'scope': SCOPES,
            'state': '_default',
            'response_type': 'code',
            'code_challenge': challenge,
            'code_challenge_method': 'S256',
            'access_type': 'offline'
        };

        // Encode the Authorization Request parameters and add them to the URL
        authUrl += queryParams(params);

        return authUrl; 
    }

    private generateVerifier() {
        this.verifier = CryptoJS.lib.WordArray.random(32).toString();
    }
    
    private generateCodeChallenge(verifier: string) {
        return CryptoJS.SHA256(verifier)
            .toString(CryptoJS.enc.Base64)
            .replace(/\+/g, '-')
            .replace(/\//g, '_')
            .replace(/=/g, '');
    }

    /*
    * If there is data stored in the session then we assume that the user is authorized by globus.
    * This is safe because even if they are able to access the extension without an authorization by globus, they'll
    * be unable to use the app because the access tokens would be invalid
    */
    attemptSignIn() {
        let data = sessionStorage.getItem('data');
        if (data) {
            globusAuthorized.resolve(JSON.parse(data));
        }
    }
}