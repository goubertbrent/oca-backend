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
from __future__ import unicode_literals

from datetime import datetime

from mcfw.properties import typed_property, unicode_property, bool_property, long_property, unicode_list_property, \
    float_property
from rogerthat.to import TO
from rogerthat.utils import parse_date
from shop.models import Customer
from solutions.common.integrations.cirklo.models import VoucherProviderId, VoucherSettings
from solutions.common.models import SolutionServiceConsent


class UpdateVoucherServiceTO(TO):
    providers = unicode_list_property('providers')


class VoucherServiceTO(UpdateVoucherServiceTO):
    name = unicode_property('name')
    service_email = unicode_property('service_email')
    creation_time = unicode_property('creation_time')
    disabled_providers = unicode_property('disabled_providers')

    @classmethod
    def from_models(cls, customer, voucher_settings, service_consent):
        # type: (Customer, VoucherSettings, SolutionServiceConsent) -> VoucherServiceTO
        to = cls()
        to.name = customer.name
        to.service_email = customer.service_email
        to.creation_time = datetime.utcfromtimestamp(customer.creation_time).isoformat() + 'Z'
        to.providers = [] if not voucher_settings else voucher_settings.providers
        to.disabled_providers = []
        if not service_consent or SolutionServiceConsent.TYPE_CIRKLO_SHARE not in service_consent.types:
            to.disabled_providers.append(VoucherProviderId.CIRKLO)
        return to


class VoucherListTO(TO):
    cursor = unicode_property('cursor')
    total = long_property('total')
    more = bool_property('more')
    results = typed_property('results', VoucherServiceTO, True)


class AppVoucher(TO):
    id = unicode_property('id')
    cityId = unicode_property('cityId')
    originalAmount = float_property('originalAmount')
    expirationDate = unicode_property('expirationDate')
    amount = float_property('amount')
    expired = bool_property('expired')

    @classmethod
    def from_cirklo(cls, id, voucher_details, current_date):
        to = cls.from_dict(voucher_details)
        to.id = id
        to.expired = current_date > parse_date(to.expirationDate)
        to.amount = to.amount / 100.0
        to.originalAmount = to.originalAmount / 100.0
        return to


class AppVoucherList(TO):
    results = typed_property('results', AppVoucher, True)
    cities = typed_property('cities', dict)
    main_city_id = unicode_property('main_city_id')


class CirkloCityTO(TO):
    city_id = unicode_property('city_id', default=None)
    logo_url = unicode_property('logo_url', default=None)

    @classmethod
    def from_model(cls, model):
        to = cls()
        if not model:
            return to
        to.city_id = model.city_id
        to.logo_url = model.logo_url
        return to
