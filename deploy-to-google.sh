set -ex
if [ `git rev-parse --abbrev-ref HEAD` != "master" ]; then
  echo 'YOU CAN ONLY DEPLOY master';
  exit 1
fi

VERSION=`cat BACKEND_VERSION`
echo 'using rogerthat-backend version' $VERSION;
pushd ../rogerthat-backend
git checkout $VERSION
popd

pushd src-frontend

npm install
gulp build --project admin --online

popd

python build.py

appcfg.py update build --oauth2
