#!/usr/bin/env bash
LISTEN_ADDRESS=0.0.0.0
BLOBSTORE_PATH=""
SEARCH_INDEXES_PATH=""
APPLICATION_ID="mobicagecloudhr"
DEV_SERVER_PATH=""
EXTRA_PARAMS=""

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

if [ -f "${DIR}/google-app-credentials.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS=${DIR}/google-app-credentials.json
fi

if [ -f "${DIR}/setenv.sh" ]; then
    . setenv.sh
fi

if [ -z ${DEV_SERVER_PATH} ]; then
  DEV_SERVER_PATH=`which dev_appserver.py`
fi

if [ ! -z ${BLOBSTORE_PATH} ]; then
    BLOBSTORE_PATH="--blobstore_path=${BLOBSTORE_PATH}"
fi

if [ ! -z ${SEARCH_INDEXES_PATH} ]; then
    SEARCH_INDEXES_PATH="--search_indexes_path=${SEARCH_INDEXES_PATH}"
fi

echo ${LISTEN_ADDRESS}
python2.7 -u ${DEV_SERVER_PATH} build --admin_host 0.0.0.0 --host ${LISTEN_ADDRESS} --port 8080 --skip_sdk_update_check --datastore_path=~/tmp/appengine.sqlite --log_level=debug ${SEARCH_INDEXES_PATH} ${BLOBSTORE_PATH} --require_indexes=yes --max_module_instances=5 --application ${APPLICATION_ID} --enable_host_checking=false --support_datastore_emulator=true ${EXTRA_PARAMS}
