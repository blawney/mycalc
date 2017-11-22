#!/bin/bash
echo "working dir:"`pwd`

# Path to a JSON credential file (service account credentials) on the docker container's filesystem
# This file allows us to authenticate with gcloud, so that we can then pull the remainder of the configuration
# files, etc. from the bucket
export CRED_FILE_PATH=$1

export PORT=$2

# start the python virtualenv
source $DJANGO_VENV/bin/activate

# get gsutil up and running.  We first authenciate with gcloud which allows us to use gcloud
$GCLOUD auth activate-service-account --key-file=$CRED_FILE_PATH
SERVICE_ACCOUNT=$(python /startup/get_account_name.py $CRED_FILE_PATH)
export BOTO_PATH=/root/.config/gcloud/legacy_credentials/$SERVICE_ACCOUNT/.boto

# copy the settings file:
gsutil cp gs://tru-t-app-resources/settings.py ./tru_t_sandbox/settings.py

# ensure that the current static files are sent to the bucket to serve them.
python /startup/copy_static_assets.py

# Start Gunicorn processes
mkdir -p /var/log/gunicorn

echo "Setting up production environment"
LOG="/var/log/gunicorn/gunicorn.log"
touch $LOG
SOCKET_PATH="unix:/host_tmp/gunicorn"$PORT".sock"  
exec gunicorn tru_t_sandbox.wsgi:application \
        --bind $SOCKET_PATH \
        --workers 3 \
        --error-logfile $LOG \
        --log-file $LOG
fi
