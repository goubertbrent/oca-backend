#!/usr/bin/env bash
set -euf
VERSION=`cat BACKEND_VERSION`
echo 'using rogerthat-backend version' ${VERSION};
pushd ../rogerthat-backend
git checkout ${VERSION}
popd

pip2 install -U --target=build/lib -r ../rogerthat-backend/requirements.txt --prefix=
npm install
npm run build
pushd build/static
npm install
popd
