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

from types import NoneType

from google.appengine.ext import deferred, db

import cloudstorage
from mcfw.rpc import arguments, returns
from rogerthat.bizz.job import delete_service
from rogerthat.bizz.job.delete_service import validate_delete_service
from rogerthat.dal import parent_key_unsafe
from rogerthat.dal.profile import get_service_profile
from rogerthat.rpc import users
from shop.dal import get_customer
from solutions.common import SOLUTION_COMMON
from solutions.common.consts import OCA_FILES_BUCKET
from solutions.common.dal import get_solution_settings
from solutions.common.utils import create_service_identity_user_wo_default


@returns(NoneType)
@arguments(service_user=users.User, delete_svc=bool)
def delete_solution(service_user, delete_svc):
    deferred.defer(_delete_solution, service_user, delete_svc, _transactional=db.is_in_transaction())


def _delete_solution(service_user, delete_svc):
    # type: (users.User, bool) -> None
    sln_settings = get_solution_settings(service_user)
    identities = [None]
    if sln_settings.identities:
        identities.extend(sln_settings.identities)
    validate_delete_service(service_user)

    def trans():
        service_profile = get_service_profile(service_user, False)
        deferred.defer(_reset_customer_model, service_user, _transactional=True)
        for service_identity in identities:
            deferred.defer(_delete_solution_models, service_user, service_identity,
                           [service_profile.solution, SOLUTION_COMMON], delete_svc, _transactional=True)
        service_profile.solution = None
        service_profile.put()
    db.run_in_transaction(trans)


def _reset_customer_model(service_user):
    from shop.bizz import re_index_customer
    customer = get_customer(service_user)
    if customer:
        customer.user_email = None
        customer.service_email = None
        customer.default_app_id = None
        customer.app_ids = []
        customer.put()

        re_index_customer(customer.key())


def _delete_solution_models(service_user, service_identity, solutions, delete_svc):
    solution = solutions.pop(0)
    _cleanup_gcs(service_user)
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    key = parent_key_unsafe(service_identity_user, solution)

    def trans():
        keys = db.GqlQuery("SELECT __key__ WHERE ANCESTOR IS KEY('%s')" % str(key)).fetch(1000)
        if keys:
            db.delete(keys)
            return True
        else:
            if solutions:
                deferred.defer(_delete_solution_models, service_user, service_identity,
                               solutions, delete_svc, _transactional=True)
            elif delete_svc and service_identity is None:
                deferred.defer(delete_service.job, service_user, service_user, _transactional=True)
            return False
    while db.run_in_transaction(trans):
        pass


def _cleanup_gcs(service_user):
    path = '/%s/services/%s' % (OCA_FILES_BUCKET, service_user.email())
    all_files = [f for f in cloudstorage.listbucket(path)]
    for f in all_files:
        cloudstorage.delete(f.filename)
