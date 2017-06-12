#!/usr/bin/env bash
VERSION=`cat BACKEND_VERSION`
echo 'using rogerthat-backend version' $VERSION;
pushd ../rogerthat-backend
git checkout $VERSION
pip install -r requirements.txt -t src/lib
pushd src/lib
zip -r lib.zip . -x "babel/*" -x "pytz/*" -x "ply/*"
shopt -s extglob # enable extended globbing to use !() with rm
rm -r -- !(lib.zip|babel|pytz|ply)
popd
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
