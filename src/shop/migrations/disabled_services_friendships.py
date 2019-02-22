# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import logging
from google.appengine.ext import db, deferred
from rogerthat.dal.profile import get_service_profile
from rogerthat.dal.service import get_friend_service_identity_connections_of_service_identity_query, \
    get_service_identities
from rogerthat.bizz.friends import breakFriendShip
from rogerthat.bizz.job import run_job
from shop.models import Customer


def disabled_services_query():
    return Customer.all(keys_only=True).filter('service_disabled_at >', 0)


def break_friendships_of_service(customer_key, dry_run=True):
    customer = db.get(customer_key)
    if not customer:
        return

    service_user = customer.service_user
    for identity in get_service_identities(service_user):
        # double check
        if get_service_profile(service_user).enabled:
            logging.warning('service %s is not disabled', service_user)
            continue

        fsics_qry = get_friend_service_identity_connections_of_service_identity_query(identity.service_identity_user)
        if fsics_qry.count(limit=1):
            logging.warning(
                'The disabled service of %s (%s) still has some connections',
                service_user.email(), identity.identifier)

            if not dry_run:
                for connection in fsics_qry:
                    deferred.defer(breakFriendShip, connection.service_identity_user, connection.friend)


def job(dry_run=True):
    run_job(disabled_services_query, [], break_friendships_of_service, [dry_run])
