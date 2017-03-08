#!/usr/bin/env bash
LISTEN_ADDRESS=0.0.0.0
BLOBSTORE_PATH=""
SEARCH_INDEXES_PATH=""

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

if [ -f "${DIR}/setenv.sh" ]; then
    . setenv.sh
fi

if [ ! -z ${BLOBSTORE_PATH} ]; then
    BLOBSTORE_PATH="--blobstore_path=${BLOBSTORE_PATH}"
fi

if [ ! -z ${SEARCH_INDEXES_PATH} ]; then
    SEARCH_INDEXES_PATH="--search_indexes_path=${SEARCH_INDEXES_PATH}"
fi

echo ${LISTEN_ADDRESS}
python2.7 -u /usr/local/google_appengine/dev_appserver.py build --admin_host 0.0.0.0 --host ${LISTEN_ADDRESS} --port 8080 --skip_sdk_update_check --datastore_path=~/tmp/appengine.sqlite --log_level=debug ${SEARCH_INDEXES_PATH} ${BLOBSTORE_PATH} --require_indexes=yes --max_module_instances=5
