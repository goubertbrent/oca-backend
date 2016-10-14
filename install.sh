#!/usr/bin/env bash
VERSION=`cat BACKEND_VERSION`
echo 'using rogerthat-backend version' $VERSION;
pushd ../rogerthat-backend
git checkout $VERSION
popd

pushd src-frontend
npm install
gulp build --project admin --online
popd
pushd src/static
npm install
popd
python build.py
