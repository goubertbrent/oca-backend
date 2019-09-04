# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.rpc import users
from rogerthat.service.api.payments import put_provider
from rogerthat.to.payment import ServicePaymentProviderFeeTO
from solutions.common.bizz.payment import get_providers_settings
from solutions.common.models import SolutionSettings


def migrate():
    run_job(_get_all_solution_settings_keys, [], _migrate_payment_settings, [])


def _get_all_solution_settings_keys():
    return SolutionSettings.all(keys_only=True)


def _migrate_payment_settings(key):
    sln_settings = db.get(key)  # type: SolutionSettings
    with users.set_user(sln_settings.service_user):
        if hasattr(sln_settings, 'payment_min_amount_for_fee'):
            min_amount = sln_settings.payment_min_amount_for_fee
            for identity in sln_settings.identities:
                settings = get_providers_settings(sln_settings.service_user, identity)
                for setting in settings:
                    if setting.provider_id == 'payconiq':
                        put_provider(setting.provider_id, setting.settings.to_dict(), identity,
                                     sln_settings.payment_test_mode, setting.enabled,
                                     ServicePaymentProviderFeeTO(amount=15,
                                                                 precision=2,
                                                                 min_amount=min_amount,
                                                                 currency='EUR'))
            remove_unused_properties(sln_settings, SolutionSettings._properties)
    sln_settings.currency = _convert_currency(sln_settings.currency)
    sln_settings.put()


def remove_unused_properties(model, allowed_properties):
    for attr in model._dynamic_properties.keys():
        if attr not in allowed_properties:
            delattr(model, attr)


def _convert_currency(currency_symbol):
    mapping = {
        u'\u20ac': u'EUR',
        u'\xa3': u'GBP',
        u'lei': u'RON',
        u'$': u'USD',
        u'': u'EUR',
    }
    if currency_symbol in mapping:
        return mapping[currency_symbol]
    else:
        raise Exception('Unknown currency %s!' % currency_symbol)
