# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
from types import NoneType

from google.appengine.ext import db
from mcfw.rpc import returns, arguments
from rogerthat.bizz.profile import create_user_profile, update_password_hash
from rogerthat.bizz.user import delete_account
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.mobile import get_user_active_mobiles
from rogerthat.dal.profile import _get_profile_not_cached, get_service_profile
from rogerthat.dal.service import get_default_service_identity_not_cached
from rogerthat.models import UserProfile
from rogerthat.rpc import users
from rogerthat.utils import bizz_check, channel, now
from rogerthat.utils.transactions import run_in_xg_transaction, allow_transaction_propagation
from shop.models import Customer
from solutions.common.dal import get_solution_settings


@returns()
@arguments(executor_user=users.User, from_user=users.User, to_user=users.User, service_email=unicode, customer_id=(int, long, NoneType))
def migrate(executor_user, from_user, to_user, service_email, customer_id=None):
    logging.info('Migrating %s to %s for customer %s', from_user.email(), to_user.email(), customer_id)

    bizz_check(from_user.email() != to_user.email(), 'FROM and TO should not be equal')

    def trans():
        from_profile = _get_profile_not_cached(from_user)
        if from_profile:
            bizz_check(isinstance(from_profile, UserProfile),
                       'Profile %s is not of expected type UserProfile, but of type %s' % (from_user, from_profile.kind()))
        else:
            logging.warn('UserProfile for %s not found! Weird...', from_user.email())

        to_put = set()
        to_profile = _get_profile_not_cached(to_user)
        if to_profile:
            bizz_check(isinstance(to_profile, UserProfile),
                       'Profile %s is not of expected type UserProfile, but of type %s' % (to_user, to_profile.kind()))

            if service_email not in to_profile.owningServiceEmails:
                to_profile.owningServiceEmails.append(service_email)
            to_put.add(to_profile)
        else:
            if from_profile:
                language = from_profile.language
                password_hash = from_profile.passwordHash
            else:
                service_profile = get_service_profile(users.User(service_email))
                language = service_profile.defaultLanguage
                password_hash = service_profile.passwordHash
            to_profile = create_user_profile(to_user, to_user.email(), language)
            to_profile.isCreatedForService = True
            to_profile.owningServiceEmails = [service_email]
            update_password_hash(to_profile, password_hash, now())

        if from_profile:
            if service_email in from_profile.owningServiceEmails:
                from_profile.owningServiceEmails.remove(service_email)
                to_put.add(from_profile)

            if not from_profile.owningServiceEmails:
                @db.non_transactional
                def has_mobiles():
                    return bool(list(get_user_active_mobiles(from_profile.user)))

                if has_mobiles():
                    from_profile.isCreatedForService = False
                    to_put.add(from_profile)
                else:
                    delete_account(from_user)

        si = get_default_service_identity_not_cached(users.User(service_email))
        si.qualifiedIdentifier = to_user.email()
        to_put.add(si)
        sln_settings = get_solution_settings(users.User(service_email))
        sln_settings.login = to_user
        sln_settings.qualified_identifier = to_user.email()
        to_put.add(sln_settings)

        if customer_id is not None:
            customer = Customer.get_by_id(customer_id)
            customer.user_email = to_user.email()
            to_put.add(customer)

        put_and_invalidate_cache(*to_put)

    allow_transaction_propagation(run_in_xg_transaction, trans)

    channel.send_message(from_user, u'rogerthat.system.dologout')
