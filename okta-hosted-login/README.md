# Example of Flask + Okta Hosted Login + GCP Workload Identity Federation

This is a fork of the Flask Okta demo. It shows you how to use Flask to log in to your application with an Okta Hosted Login page.  The login is achieved through the [authorization code flow](https://developer.okta.com/authentication-guide/implementing-authentication/auth-code), where the user is redirected to the Okta-Hosted login page. After the user authenticates, they are redirected back to the application with an access code that is then exchanged for an access token and an an OIDC ID token. 

After token validation the application creates a GCP credentials configuration that defines how the OIDC ID token will be exchanged for a GCP federated token. This credential configuration can be passed as an argument to GCP API's, in this example GCS APIs. The GCS (and all other GCP) libraries transparently handle the token exchange from OIDC id token to GCP federated token as well as the authentication.

What is interesting is that you can use federated 'placeholder' principals in GCP that map to Okta user group names as for example principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/group/OKTA_GROUP_ID. You can assign GCP IAM roles to these 'placeholder' principals. In this example, if you add an Okta user and assign the correct user group in Okta, the user will automatically be able to access the set of GCS objects that correspond to his group. There is no need to add and configure a principal in GCP for that user to get GCS access as long as the assigned user group is correct.   

In this example we have three buckets, one each for the Okta groups 'admin', 'user' and 'any'. Each user will only 'see' the respective buckets for his group. While this example is based on the user group, you can define up to 50 attributes and use these attributes in IAM principalSet:// role bindings to grant access to all identities with a certain set of attributes. This is described in detail [here](https://cloud.google.com/iam/docs/workload-identity-federation).

> Requires Python version 3.6.0 or higher.

## Prerequisites

Before running this sample, you will need the following:

* An Okta Developer Account, you can sign up for one at https://developer.okta.com/signup/.
* An Okta Application configured for Web mode. You can create one from the Okta Developer Console, and you can find instructions [here][OIDC WEB Setup Instructions].  When following the wizard, use the default properties.  They are designed to work with our sample applications.

## Running This Example

To run this application, you first need to clone this repo:

```bash
git clone git@github.com:okta/samples-python-flask.git
cd samples-python-flask
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

Open the `okta-hosted-login` directory and copy the [`client_secrets.json.dist`](client_secrets.json.dist) to `client_secrets.json`:

```bash
cd okta-hosted-login
cp client_secrets.json.dist client_secrets.json
```

You now need to gather the following information from the Okta Developer Console:

- **Client ID** and **Client Secret** - These can be found on the "General" tab of the Web application that you created earlier in the Okta Developer Console.
- **Issuer** - This is the URL of the authorization server that will perform authentication.  All Developer Accounts have a "default" authorization server.  The issuer is a combination of your Org URL (found in the upper right of the console home page) and `/oauth2/default`. For example, `https://dev-1234.oktapreview.com/oauth2/default`.

Fill in the information that you gathered in the `client_secrets.json` file.

```json
{
  "auth_uri": "https://{yourOktaDomain}/oauth2/default/v1/authorize",
  "client_id": "{yourClientId}",
  "client_secret": "{yourClientSecret}",
  "redirect_uri": "http://localhost:8080/authorization-code/callback",
  "issuer": "https://{yourOktaDomain}/oauth2/default",
  "token_uri": "https://{yourOktaDomain}/oauth2/default/v1/token",
  "token_introspection_uri": "https://{yourOktaDomain}/oauth2/default/v1/introspect",
  "userinfo_uri": "https://{yourOktaDomain}/oauth2/default/v1/userinfo"
}
```

Start the app server:

```
python main.py
```

Now navigate to http://localhost:8080 in your browser.

If you see a home page that prompts you to log in, then things are working! Clicking the **Log in** button will redirect you to the Okta hosted sign-in page.

You can log in with the same account that you created when signing up for your Developer Org. You can also use a known username and password from your Okta Directory.

**Note:** If you are currently using your Developer Console, you already have a Single Sign-On (SSO) session for your Org. You will be automatically logged into your application as the same user that is using the Developer Console. You may want to use an incognito tab to test the flow from a blank slate.

[OIDC Web Setup Instructions]: https://developer.okta.com/authentication-guide/implementing-authentication/auth-code#1-setting-up-your-application
