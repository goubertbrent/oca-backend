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

from google.appengine.api import search
from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.bizz.maps.services import _delete_index, _create_index
from rogerthat.bizz.service import SERVICE_INDEX, SERVICE_LOCATION_INDEX, re_index, re_index_map_only
from rogerthat.consts import HIGH_LOAD_WORKER_QUEUE
from rogerthat.dal.profile import is_trial_service
from rogerthat.models import ServiceIdentity
from rogerthat.utils import drop_index
from rogerthat.utils.service import get_service_user_from_service_identity_user


def job(queue=HIGH_LOAD_WORKER_QUEUE):
    svc_index = search.Index(name=SERVICE_INDEX)
    loc_index = search.Index(name=SERVICE_LOCATION_INDEX)

    drop_index(svc_index)
    drop_index(loc_index)
    
    _delete_index()
    _create_index()

    run_job(query, [], worker, [], worker_queue=queue)
    

def job_map(queue=HIGH_LOAD_WORKER_QUEUE):
    _delete_index()
    _create_index()

    run_job(query, [], worker_map, [], worker_queue=queue)


def query():
    return ServiceIdentity.all(keys_only=True)


def worker(si_key):
    si = db.get(si_key)
    service_user = get_service_user_from_service_identity_user(si.service_identity_user)
    if is_trial_service(service_user):
        return
    re_index(si.service_identity_user)


def worker_map(si_key):
    si = db.get(si_key)
    service_user = get_service_user_from_service_identity_user(si.service_identity_user)
    if is_trial_service(service_user):
        return
    re_index_map_only(si.service_identity_user)
