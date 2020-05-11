# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

from google.appengine.ext import db
from rogerthat.bizz.job import run_job
from rogerthat.models import UserProfile


def job():
    run_job(_get_all_users, [], _update_roles, [])


def _get_all_users():
    return UserProfile.all(keys_only=True)


def _update_roles(up_key):
    def trans():
        user_profile = db.get(up_key)
        service_roles = []
        for role, service in zip(user_profile.roles, user_profile.role_services):
            if role.startswith('sr:'):
                role = role.replace('sr:', '')
            service_roles.append(u"%s:%s" % (service, role))
        user_profile.roles = []
        user_profile.role_services = []
        user_profile.service_roles = service_roles
        user_profile.put()
    db.run_in_transaction(trans)
