import requests
import random
import string
import json
import os

from flask import Flask, render_template, redirect, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from google.auth import identity_pool
from helpers import is_access_token_valid, is_id_token_valid, config, list_objects
from user import User


app = Flask(__name__)
app.config.update({'SECRET_KEY': ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=32))})

login_manager = LoginManager()
login_manager.init_app(app)


APP_STATE = 'ApplicationState'
NONCE = 'SampleNonce'

envvar = os.environ.get("WORKLOAD_IDENTITY_POOL_PROVIDER_ID")
if envvar is not None:
        pass
else:
        print("Please edit and source setvar to set environment variables and retry\n")
        exit()



@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login")
def login():
    # get request params
    query_params = {'client_id': config["client_id"],
                    'redirect_uri': config["redirect_uri"],
                    'scope': "openid email profile",
                    'state': APP_STATE,
                    'nonce': NONCE,
                    'response_type': 'code',
                    'response_mode': 'query'}

    # build request_uri
    request_uri = "{base_url}?{query_params}".format(
        base_url=config["auth_uri"],
        query_params=requests.compat.urlencode(query_params)
    )

    return redirect(request_uri)


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@app.route("/authorization-code/callback")
def callback():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    code = request.args.get("code")
    if not code:
        return "The code was not returned or is not accessible", 403
    query_params = {'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': request.base_url
                    }
    query_params = requests.compat.urlencode(query_params)
    exchange = requests.post(
        config["token_uri"],
        headers=headers,
        data=query_params,
        auth=(config["client_id"], config["client_secret"]),
    ).json()

    # Get tokens and validate
    if not exchange.get("token_type"):
        return "Unsupported token type. Should be 'Bearer'.", 403
    access_token = exchange["access_token"]
    id_token = exchange["id_token"]

    if not is_access_token_valid(access_token, config["issuer"]):
        return "Access token is invalid", 403

    if not is_id_token_valid(id_token, config["issuer"], config["client_id"], NONCE):
        return "ID token is invalid", 403

    # Write Okta's OIDC id token to tmp files so that it can later be exchanged for a GCP federated token
    random_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    okta_oidc_credential_file_name = "/tmp/" + random_id + "_okta_oidc_cred"
    with open(okta_oidc_credential_file_name, 'w', encoding='utf-8') as f:
        f.write(id_token)

    # Authorization flow successful, get userinfo and login user
    userinfo_response = requests.get(config["userinfo_uri"],
                                     headers={'Authorization': f'Bearer {access_token}'}).json()

    unique_id = userinfo_response["sub"]
    user_email = userinfo_response["email"]
    user_name = userinfo_response["given_name"]

    user = User(
        id_=unique_id, name=user_name, email=user_email
    )

    if not User.get(unique_id):
        User.create(unique_id, user_name, user_email)

    # Read environment variable for the audience
    project_number = os.getenv('PROJECT_NUMBER')
    workload_identity_pool_id = os.getenv('WORKLOAD_IDENTITY_POOL_ID')
    workload_identity_pool_provider_id = os.getenv('WORKLOAD_IDENTITY_POOL_PROVIDER_ID')

    # Create GCP federation credential config 
    audience_str = "//iam.googleapis.com/projects/"+project_number+"/locations/global/workloadIdentityPools/"+workload_identity_pool_id+"/providers/"+workload_identity_pool_provider_id

    gcp_credential_dict = {
        "type": "external_account",
        "audience": audience_str,
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        "token_url": "https://sts.googleapis.com/v1/token",
        "credential_source": {
            "file": okta_oidc_credential_file_name
        },
    }

    # Set Oauth scope for GCS as per https://developers.google.com/identity/protocols/oauth2/scopes#storage
    scopes = ['https://www.googleapis.com/auth/devstorage.full_control']

	# Create a credentials object - see https://google-auth.readthedocs.io/en/master/reference/google.auth.identity_pool.html
    credentials = identity_pool.Credentials.from_info(gcp_credential_dict)
    scoped_credentials = credentials.with_scopes(scopes)

    project = os.getenv('PROJECT_ID')
    allblobs = list_objects(project, scoped_credentials)

    # Turn list into a dictionary for Jinja template
    enum=enumerate(allblobs)
    objectdict = dict((index, objname) for index, objname in enum)

    # Delete the id token in tmp
    os.remove(okta_oidc_credential_file_name)

    login_user(user)

    # Show the list of accessible objects
    return render_template("objlist.html", objectdict=objectdict, user=current_user)

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True)
