#!/bin/bash -x
#### Source setvars before calling this script !!!! ####

# Create the workload identity pool
gcloud iam workload-identity-pools create "$WORKLOAD_IDENTITY_POOL_ID" --location="global" \
--description "Workload pool for Okta demo" --display-name "$WORKLOAD_IDENTITY_POOL_ID"

# Create the workload identity pool provider
gcloud iam workload-identity-pools providers create-oidc $WORKLOAD_IDENTITY_POOL_PROVIDER_ID --location="global" \
--workload-identity-pool "$WORKLOAD_IDENTITY_POOL_ID" --issuer-uri "$ISSUER_URL" \
--allowed-audiences "$AUDIENCE" --attribute-mapping "google.subject=assertion.sub,google.groups=assertion.Groups"

# Create bucket and set ACL as private giving the bucket owner OWNER permission for a bucket or object.
gsutil mb gs://$BUCKET_PREFIX-any
gsutil mb gs://$BUCKET_PREFIX-user
gsutil mb gs://$BUCKET_PREFIX-admin

# Create a random number of files in each bucket
for i in any user admin
do
	num_files=$(echo $(( $RANDOM % 10 )))
	for j in $(seq 1 1 $num_files)
	do
		dd if=/dev/urandom of=/tmp/object-$i-$j bs=512 count=1
		gsutil cp /tmp/object-$i-$j gs://$BUCKET_PREFIX-$i
	done
done

# Add the right permissions for the buckets
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_PREFIX-any --member=principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$WORKLOAD_IDENTITY_POOL_ID/group/any --role=roles/storage.objectViewer

gcloud storage buckets add-iam-policy-binding gs://$BUCKET_PREFIX-user --member=principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$WORKLOAD_IDENTITY_POOL_ID/group/user --role=roles/storage.objectViewer

gcloud storage buckets add-iam-policy-binding gs://$BUCKET_PREFIX-admin --member=principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$WORKLOAD_IDENTITY_POOL_ID/group/admin --role=roles/storage.objectViewer
