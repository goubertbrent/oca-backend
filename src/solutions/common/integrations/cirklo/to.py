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

from typing import List

from mcfw.properties import typed_property, unicode_property, bool_property, long_property, float_property
from rogerthat.to import TO
from rogerthat.utils import parse_date
from shop.models import Customer
from solutions.common.integrations.cirklo.models import VoucherProviderId, VoucherSettings
from solutions.common.models import SolutionServiceConsent


class UpdateVoucherServiceTO(TO):
    provider = unicode_property('provider')
    enabled = bool_property('enabled')


class VoucherProviderTO(TO):
    provider = unicode_property('provider')
    enabled = bool_property('enabled')
    can_enable = bool_property('can_enable')
    enable_date = unicode_property('enable_date')

    @classmethod
    def from_model(cls, provider, can_enable, model):
        return cls(provider=provider,
                   enabled=model is not None,
                   can_enable=can_enable,
                   enable_date=model and (model.enable_date.isoformat() + 'Z'))


class VoucherServiceTO(TO):
    name = unicode_property('name')
    service_email = unicode_property('service_email')
    creation_time = unicode_property('creation_time')
    providers = typed_property('providers', VoucherProviderTO, True)  # type: List[VoucherProviderTO]

    @classmethod
    def from_models(cls, customer, voucher_settings, service_consent):
        # type: (Customer, VoucherSettings, SolutionServiceConsent) -> VoucherServiceTO
        to = cls()
        to.name = customer.name
        to.service_email = customer.service_email
        to.creation_time = datetime.utcfromtimestamp(customer.creation_time).isoformat() + 'Z'
        to.providers = []
        for provider in VoucherProviderId.all():
            if provider == VoucherProviderId.CIRKLO:
                can_enable = service_consent and SolutionServiceConsent.TYPE_CIRKLO_SHARE in service_consent.types
            else:
                can_enable = False # should never happen
            settings = voucher_settings and voucher_settings.get_provider(provider)
            to.providers.append(VoucherProviderTO.from_model(provider, can_enable, settings))
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
