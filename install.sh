#!/usr/bin/env bash
VERSION=`cat BACKEND_VERSION`
echo 'using rogerthat-backend version' $VERSION;
pushd ../rogerthat-backend
git checkout $VERSION
pip install -r requirements.txt -t src/lib
popd

npm install
pushd src/static
npm install
popd
python build.py
