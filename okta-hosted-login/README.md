# Example of Flask + Okta Hosted Login + GCP Workload Identity Federation

This is a fork of the okta-hosted-login subdirectory of the [Flask Okta demo](https://github.com/okta/samples-python-flask). It shows you how to use Flask to log into your application with an Okta Hosted Login page.  The login is achieved through the [authorization code flow](https://developer.okta.com/authentication-guide/implementing-authentication/auth-code), where the user is redirected to the Okta-Hosted login page. After the user authenticates, they are redirected back to the application with an access code that is then exchanged for an access token and an an OIDC ID token. 

After token validation the application creates a GCP credentials configuration that defines how the OIDC ID token will be exchanged for a GCP federated token. This credential configuration can be passed as an argument to GCP API's, in this example GCS APIs. The GCS libraries (and all other GCP libraries) transparently handle the token exchange from OIDC id token to GCP federated token as well as the authentication.

What is more interesting than the token exchange flow is that is facilitates the mapping of Okta users to federated GCP principals. You can assign GCP IAM roles to these federated principals just as you can assign them to regular user identities. In this example we map to a federated GCP token through the Okta group name. We have three buckets, each for one of the Okta groups 'admin', 'user' and 'any'. Each bucket allows for read access for the respective principal set. 

 ```principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/group/{admin, user, any}```

If you add an Okta user and assign the correct user group in Okta, that user will automatically be able to access the set of GCS objects that correspond to his group. There is no need to add and configure a principal in GCP. Only the group assignment in Okta matters. While this example is based on the Okta user group, you can also use other Okta attributes including custom attributes. You can define up to 50 attributes and use them in IAM principalSet:// role bindings. This is described in detail [here](https://cloud.google.com/iam/docs/workload-identity-federation).

> This setup has been tested with Python version 3.11.2 

## Prerequisites

Before running this sample, you will need the following:

* An Okta Developer Account, you can sign up for one at https://developer.okta.com/signup/ (Access the Okta Developer Edition Service).  
* An Okta Application configured for Web mode. You can create one from the Okta Developer Console, and you can find instructions [here][OIDC WEB Setup Instructions].  When following the wizard, use the default properties. Check 'Client acting on behalf of itself | Client Credentials' and 'Client acting on behalf of a user | Authorization Code'. Select 'Allow everyone in your organization to access' and 'Enable immediate access with Federation Broker Mode'. They are designed to work with our sample applications
* Three custom Okta user groups named 'any', 'user' and 'admin'
* At least two configured Okta users, each in one or more of these groups
* Group claims added to your default authorization server - Go to 'Security | API' and click on the default authorization server - Go to Claims and click on 'Add Claim'
![image](https://github.com/marin102/samples-python-flask-gcp-workload-id-fed/assets/136770873/56e396de-fb64-4ff5-b502-dfd88e3d4121)
* Google Cloud SDK - Libraries and Command Line Tools installed on your local system - ensure that you have the right [IAM roles for workload identity federation](https://cloud.google.com/iam/docs/understanding-roles#workload-identity-pools-roles). It is easiest if you have the project owner role for your project

## Setting up Flask, Okta and GCP Workload Identity Federation

To run this application, you first need to clone this repo:

```bash
git clone https://github.com/marin102/samples-python-flask-gcp-workload-id-fed.git
cd samples-python-flask-gcp-workload-id-fed/okta-hosted-login
```

Then install dependencies (You may want to use a virtual Python environment):

```bash
pip install -r requirements.txt
```

Copy the [`client_secrets.json.dist`](client_secrets.json.dist) to `client_secrets.json`:

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
Copy file `blank_setvars` to `setvars` and edit the environment variables

```
export PROJECT_ID="myproject"                                                                 	# Name of the GCP project
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="get(projectNumber)")        
export PROJECT_NUMBER
export BUCKET_PREFIX="okta-gcp-wif"								# Prefix for the three buckets that are created with suffixes admin, any, user
export WORKLOAD_IDENTITY_POOL_ID="okta-gcp-wif"							# The name of the workload identity pool 
export WORKLOAD_IDENTITY_POOL_PROVIDER_ID="okta-gcp-wif-provider"				# The name of the workload identity pool provider
export ISSUER_URL="https://dev-12345678.okta.com/oauth2/default"				# The URL of the issuer - same as in issuer field in client_secrets.json 
export AUDIENCE="12345678912345678900"								# The Okta Client ID for the application
```

Log into your GCP account

```gcloud auth login```

Source the file with the environment variables

```. ./setvars```

Launch ```setup.sh``` which creates three buckets for each group with between 1 and 10 small files with random content

```./setup.sh```

Start the app server

```
python main.py
```

Now navigate to http://localhost:8080 in your browser.

If you see a home page that prompts you to log in, then things are working! Clicking the **Log in** button will redirect you to the Okta hosted sign-in page.

You can log in with the same account that you created when signing up for your Developer Org. You can also use a known username and password from your Okta Directory.

**Note:** If you are currently using your Developer Console, you already have a Single Sign-On (SSO) session for your Org. You will be automatically logged into your application as the same user that is using the Developer Console. You may want to use an incognito tab to test the flow from a blank slate.

[OIDC Web Setup Instructions]: https://developer.okta.com/authentication-guide/implementing-authentication/auth-code#1-setting-up-your-application
