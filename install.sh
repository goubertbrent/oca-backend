#!/usr/bin/env bash
VERSION=`cat BACKEND_VERSION`
echo 'using rogerthat-backend version' $VERSION;
pushd ../rogerthat-backend
git checkout $VERSION
popd
build_type=$1
if [ -z ${build_type} ]; then
  build_type="--dev"
fi

pushd src-frontend
npm install
bower install --allow-root
gulp build --project admin ${build_type}
popd
npm install
pushd src/static
npm install
popd
python build.py
