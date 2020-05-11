#!/usr/bin/env bash
set -ex

CUR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_COLOR="\033[1;34m\n\n"
ERR_COLOR="\033[1;31m\n\n"
NO_COLOR="\n\033[0m"

if [ -z "$GAE" ]; then
  GAE="/usr/local/google_appengine/"
fi

if [ ! -d "$GAE" ]; then
  echo -e "${ERR_COLOR}!Could not find google_appengine folder!${NO_COLOR}"
  exit 1
fi

pushd ${CUR_DIR}
PYTHONPATH=src-test:src:${CUR_DIR}/build/lib:$GAE:$GAE/lib/jinja2-2.6/:$GAE/lib/yaml/lib/:$GAE/lib/webob_0_9/:$GAE/lib/webapp2-2.5.2/:$GAE/lib/django-1.4/:$GAE/lib/jinja2-2.6/ nosetests -w src-test/rogerthat_tests --all-modules -vv --attr=assertAlmostEqual
PYTHONPATH=src-test:src:${CUR_DIR}/build/lib:$GAE:$GAE/lib/jinja2-2.6/:$GAE/lib/yaml/lib/:$GAE/lib/webob_0_9/:$GAE/lib/webapp2-2.5.2/:$GAE/lib/django-1.4/:$GAE/lib/jinja2-2.6/ nosetests -w src-test/test --all-modules -vv --attr=assertAlmostEqual
popd
