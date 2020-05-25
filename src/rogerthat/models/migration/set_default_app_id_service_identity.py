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

from google.appengine.ext import db
from rogerthat.bizz.job import run_job
from rogerthat.models import ServiceIdentity


def job_set_default_app_id_on_service_identity():
    run_job(_get_service_identity_keys, [], _task_set_default_app_id, [])


def _get_service_identity_keys():
    return ServiceIdentity.all(keys_only=True)


def _task_set_default_app_id(service_identity_key):
    def trans():
        si = db.get(service_identity_key)
        si.defaultAppId = si.app_id
        si.put()
    db.run_in_transaction(trans)