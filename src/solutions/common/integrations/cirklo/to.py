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

from typing import List

from mcfw.properties import typed_property, unicode_property, bool_property, long_property, float_property, \
    unicode_list_property
from rogerthat.to import TO
from rogerthat.utils import parse_date


class WhitelistVoucherServiceTO(TO):
    id = unicode_property('id')
    email = unicode_property('email')
    accepted = bool_property('accepted')


def _get_search_data(whitelist_date, denied, merchant_registered, source):
    search_data = []
    if whitelist_date:
        search_data.append(u'whitelisted')
    elif denied:
        search_data.append(u'denied')
    else:
        search_data.append(u'pending')

    if merchant_registered:
        search_data.append(u'merchant_registered')
    else:
        search_data.append(u'merchant_not_registered')

    search_data.append(source)

    return search_data


class CirkloVoucherServiceTO(TO):
    id = unicode_property('id')
    creation_date = unicode_property('creation_date')
    name = unicode_property('name')
    email = unicode_property('email')
    address = unicode_property('address')
    whitelist_date = unicode_property('whitelist_date')
    merchant_registered = bool_property('merchant_registered')
    denied = bool_property('denied')
    phone_number = unicode_property('phone_number', default=None)
    search_data = unicode_list_property('search_data')

    @classmethod
    def from_model(cls, m, whitelist_date, merchant_registered, source):
        to = cls(id=unicode(m.key.id()),
                 creation_date=m.creation_date.isoformat() + 'Z',
                 whitelist_date=whitelist_date,
                 merchant_registered=merchant_registered,
                 denied=m.denied,
                 search_data=_get_search_data(whitelist_date, m.denied, merchant_registered, source))
        if m.data:
            to.name = m.data['company']['name']
            to.email = m.data['company']['email']
            to.address = ', '.join([' '.join([m.data['company']['address_street'], m.data['company']['address_housenumber']]),
                                    m.data['company']['address_postal_code'],
                                    m.data['company']['address_city']])
        return to

    def populate_from_info(self, service_info, customer):
        self.name = service_info.name
        self.email = customer.user_email
        self.address = customer.full_address_string
        self.phone_number = service_info.main_phone_number
        return self

    @classmethod
    def from_cirklo_info(cls, cirklo_merchant):
        merchant_registered = 'shopInfo' in cirklo_merchant
        name = u''
        address = u''
        if merchant_registered:
            shop_info = cirklo_merchant['shopInfo']
            name = shop_info['shopName']
            address = u'%s %s' % (shop_info['streetName'], shop_info['streetNumber'])
        return cls(id='external_%s' % cirklo_merchant['id'],
                   creation_date=cirklo_merchant['createdAt'],
                   name=name,
                   email=cirklo_merchant['email'],
                   address=address,
                   whitelist_date=cirklo_merchant['createdAt'],
                   merchant_registered=merchant_registered,
                   denied=False,
                   search_data=_get_search_data(cirklo_merchant['createdAt'], False, merchant_registered,
                                                u'Cirklo database'))


class CirkloVoucherListTO(TO):
    cursor = unicode_property('cursor')
    total = long_property('total')
    more = bool_property('more')
    results = typed_property('results', CirkloVoucherServiceTO, True)  # type: List[CirkloVoucherServiceTO]


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


class SignupLanguagePropertyTO(TO):
    nl = unicode_property('nl', default=None)
    fr = unicode_property('fr', default=None)


class SignupMailsTO(TO):
    accepted = typed_property('accepted', SignupLanguagePropertyTO)
    denied = typed_property('denied', SignupLanguagePropertyTO)


class CirkloAppInfoTO(TO):
    enabled = bool_property('enabled')
    title = typed_property('title', dict)
    buttons = typed_property('buttons', dict, True)


class CirkloCityTO(TO):
    city_id = unicode_property('city_id', default=None)
    logo_url = unicode_property('logo_url', default=None)
    signup_enabled = bool_property('signup_enabled')
    signup_logo_url = unicode_property('signup_logo_url', default=None)
    signup_name_nl = unicode_property('signup_name_nl', default=None)
    signup_name_fr = unicode_property('signup_name_fr', default=None)
    signup_mail = typed_property('signup_mail', SignupMailsTO)  # type: SignupMailsTO
    app_info = typed_property('app_info', CirkloAppInfoTO)  # type: CirkloAppInfoTO

    @classmethod
    def from_model(cls, model):
        to = cls()
        if not model:
            return to
        to.city_id = model.city_id
        to.logo_url = model.logo_url
        to.signup_enabled = model.signup_enabled
        to.signup_logo_url = model.signup_logo_url
        to.signup_name_nl = model.signup_names.nl if model.signup_names else None
        to.signup_name_fr = model.signup_names.fr if model.signup_names else None
        to.signup_mail = SignupMailsTO()
        to.signup_mail.accepted = SignupLanguagePropertyTO()
        to.signup_mail.denied = SignupLanguagePropertyTO()
        if model.signup_mail:
            to.signup_mail.accepted = SignupLanguagePropertyTO.from_model(model.signup_mail.accepted)
            to.signup_mail.denied = SignupLanguagePropertyTO.from_model(model.signup_mail.denied)
        if model.app_info:
            app_info = CirkloAppInfoTO()
            app_info.enabled = model.app_info.enabled
            app_info.title = model.app_info.title
            app_info.buttons = model.app_info.buttons
            to.app_info = app_info
        else:
            to.app_info = CirkloAppInfoTO()
            to.app_info.enabled = False
            to.app_info.title = {
                'en': '### Order your voucher now 🛍️',
                'nl': '### Koop nu je cadeaubon 🛍️',
                'fr': '### Achetez maintenant votre chèque-cadeau 🛍️',
            }
            to.app_info.buttons = []
        return to
