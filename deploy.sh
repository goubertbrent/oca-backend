#!/usr/bin/env bash
set -e

now="$(date +'%Y%m%dt%H%M%S')"

CUR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_COLOR="\033[1;34m\n\n"
ERR_COLOR="\033[1;31m\n\n"
NO_COLOR="\n\033[0m"

echo -e "${LOG_COLOR}* Deploying to Google Cloud${NO_COLOR}"

pushd ${CUR_DIR}

pushd src
gcloud app deploy app_backend.yaml --project rogerthat-server --quiet --no-promote --version $now
gcloud app deploy app.yaml --project rogerthat-server --quiet --no-promote --version $now
popd

popd