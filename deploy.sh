#!/usr/bin/env bash
set -e

if [ "$#" -ne 1 ]
then
  version_name="$(date +'%Y%m%dt%H%M%S')"
else
  version_name=$1
fi

CUR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_COLOR="\033[1;34m\n\n"
NO_COLOR="\n\033[0m"

echo -e "${LOG_COLOR}* Deploying to Google Cloud${NO_COLOR}"

pushd "${CUR_DIR}"

pushd src
gcloud app deploy app_backend.yaml --project rogerthat-server --quiet --no-promote --version "$version_name"
gcloud app deploy app.yaml --project rogerthat-server --quiet --no-promote --version "$version_name"
popd

popd
