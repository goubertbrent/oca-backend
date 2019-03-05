#!/usr/bin/env bash
set -euf
VERSION=`cat BACKEND_VERSION`
echo 'using mobicage-backend version' ${VERSION};
pushd ../mobicage-backend
#git checkout ${VERSION}
popd

requirements1=`cat ../mobicage-backend/requirements.txt`
requirements2=`cat requirements.txt`
requirements="${requirements1} ${requirements2}"

pip2 install -U --target=build/lib ${requirements} --prefix=
npm install
npm run build
pushd build/static
npm install
popd
pushd client/oca-forms
npm install
npm run build
popd
