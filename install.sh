#!/usr/bin/env bash
set -euf
VERSION=`cat BACKEND_VERSION`
echo 'using mobicage-backend version' ${VERSION};
pushd ../mobicage-backend
#git checkout ${VERSION}
popd

pip2 install -U --target=build/lib -r ../mobicage-backend/requirements.txt --prefix=
npm install
npm run build
pushd build/static
npm install
popd
