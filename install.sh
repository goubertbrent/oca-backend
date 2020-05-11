#!/usr/bin/env bash
set -euf

pip2 install --target=src/lib -r requirements.txt --prefix=
pushd src/static
npm install
popd
pushd client
npm install
npm run build
popd
