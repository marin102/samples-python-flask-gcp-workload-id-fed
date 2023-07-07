import asyncio
import json
import os
from google.cloud import storage

from okta_jwt_verifier import AccessTokenVerifier, IDTokenVerifier


loop = asyncio.get_event_loop()


def is_access_token_valid(token, issuer):
    jwt_verifier = AccessTokenVerifier(issuer=issuer, audience='api://default')
    try:
        loop.run_until_complete(jwt_verifier.verify(token))
        return True
    except Exception:
        return False


def is_id_token_valid(token, issuer, client_id, nonce):
    jwt_verifier = IDTokenVerifier(issuer=issuer, client_id=client_id, audience='api://default')
    try:
        loop.run_until_complete(jwt_verifier.verify(token, nonce=nonce))
        return True
    except Exception:
        return False

def list_objects(project, scoped_credentials):
    storage_client = storage.Client(project=project, credentials=scoped_credentials)
            
    bucket_prefix = os.getenv('BUCKET_PREFIX')
    bucket_name_list = [bucket_prefix+"-any", bucket_prefix+"-user", bucket_prefix+"-admin"]
    blob_name_list = []

    # We iterate over the three buckets ignore 403's and other errors
    for bucket_name in bucket_name_list:
        bucket = storage_client.bucket(bucket_name)
        try:
            for blobs in bucket.list_blobs():
                blob_name_list.append(blobs.name)
        except:
            continue
        
    return blob_name_list

def load_config(fname='./client_secrets.json'):
    config = None
    with open(fname) as f:
        config = json.load(f)
    return config

config = load_config()
