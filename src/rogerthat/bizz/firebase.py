# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
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
# @@license_version:1.7@@

import base64
import json

from mcfw.exceptions import HttpBadRequestException
from rogerthat.models.firebase import FirebaseProjectSettings


def get_firebase_projects():
    l = []
    for fps in FirebaseProjectSettings.query():
        l.append({
            'project_id': fps.project_id
        })
    return l


def create_firebase_project(base64_str):
    service_account_key = json.loads(base64.b64decode(base64_str))
    
    for k in ('client_x509_cert_url',
              'auth_uri',
              'private_key',
              'client_email',
              'private_key_id',
              'client_id',
              'token_uri',
              'project_id',
              'type',
              'auth_provider_x509_cert_url'):

        v = service_account_key.get(k)
        if not v:
            raise HttpBadRequestException('bad_file', data={'message': 'Bad file upload'})
    if service_account_key['type'] != 'service_account':
        raise HttpBadRequestException('bad_file', data={'message': 'Bad file upload'})
    project_id = service_account_key['project_id']

    fps_key = FirebaseProjectSettings.create_key(project_id)
    if fps_key.get():
        raise HttpBadRequestException('duplicate_project', data={'message': 'This project already exists'})

    fps = FirebaseProjectSettings(key=fps_key)
    fps.service_account_key = service_account_key
    fps.put()

    return {
        'project_id': project_id
    }
