#!/usr/bin/env bash
set -ex

CUR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_COLOR="\033[1;34m\n\n"
ERR_COLOR="\033[1;31m\n\n"
NO_COLOR="\n\033[0m"

if [ ! -d "${CUR_DIR}/../mobicage-backend/" ]; then
  echo -e "${ERR_COLOR}!Could not find mobicage-backend repo!${NO_COLOR}"
  exit 1
fi

if [ -z "$GAE" ]; then
  GAE="/usr/local/google_appengine/"
fi

if [ ! -d "$GAE" ]; then
  echo -e "${ERR_COLOR}!Could not find google_appengine folder!${NO_COLOR}"
  exit 1
fi

pushd ${CUR_DIR}

echo -e "${LOG_COLOR}* Merging mobicage-backend and solutions${NO_COLOR}"
npm run build

echo -e "${LOG_COLOR}* Running unit-tests of solutions${NO_COLOR}"
PYTHONPATH=src-test:build::build/lib:${CUR_DIR}/../mobicage-backend/src-test:$GAE:$GAE/lib/jinja2-2.6/:$GAE/lib/yaml/lib/:$GAE/lib/webob_0_9/:$GAE/lib/webapp2-2.5.2/:$GAE/lib/django-1.4/:$GAE/lib/jinja2-2.6/ nosetests -w src-test/test --all-modules -vv --attr=assertAlmostEqual

popd

echo -e "${LOG_COLOR}* Running unit-tests of mobicage-backend${NO_COLOR}"
pushd ${CUR_DIR}/../mobicage-backend/
PYTHONPATH=src-test:src:${CUR_DIR}/build/lib:$GAE:$GAE/lib/jinja2-2.6/:$GAE/lib/yaml/lib/:$GAE/lib/webob_0_9/:$GAE/lib/webapp2-2.5.2/:$GAE/lib/django-1.4/:$GAE/lib/jinja2-2.6/ nosetests -w src-test/rogerthat_tests --all-modules -vv --attr=assertAlmostEqual
popd
