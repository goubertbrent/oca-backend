# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.5@@
from os import environ

# Example environ copied from live env

# environ = {
#     'GAE_MEMORY_MB': '256',
#     'GAE_INSTANCE': '00c61b117cb61de63e23fc6239dd0ccf3c50f8897f2676ef2cb04a39b446e8e18bd49c8eda2d',
#     'HOME': '/root',
#     'PORT': '8081',
#     'PYTHONUNBUFFERED': '1',
#     'PYTHONDONTWRITEBYTECODE': '1',
#     'GAE_SERVICE': 'oca',
#     'SERVER_SOFTWARE': 'gunicorn/20.0.4',
#     'PATH': '/layers/google.python.pip/pip/bin:/layers/google.python.webserver/gunicorn/bin:/env/bin:/opt/python3.8/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
#     'GAE_DEPLOYMENT_ID': '429352662071873609',
#     'FIRESTORE_PROJECT': 'our-city-app',
#     'DEBIAN_FRONTEND': 'noninteractive',
#     'GOOGLE_CLOUD_PROJECT': 'rogerthat-server',
#     'GAE_ENV': 'standard',
#     'VIRTUAL_ENV': '/env',
#     'PWD': '/srv',
#     'GAE_APPLICATION': 'e~rogerthat-server',
#     'GAE_RUNTIME': 'python38',
#     'PYTHONPATH': '/layers/google.python.pip/pip:/layers/google.python.webserver/gunicorn',
#     'GAE_VERSION': '20200907t092017',
#     'LC_CTYPE': 'C.UTF-8'
# }

DEBUG = environ.get('SERVER_SOFTWARE', 'Development') == 'Development'
FIRESTORE_PROJECT = environ.get('FIRESTORE_PROJECT', 'oca-development')
PORT = int(environ.get('PORT', '8333'))
APPLICATION_ID = environ.get('GOOGLE_CLOUD_PROJECT', 'development')
