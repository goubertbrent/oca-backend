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

import logging
from datetime import datetime

from google.appengine.ext import ndb, deferred

from mcfw.cache import invalidate_cache
from mcfw.consts import REST_TYPE_TO
from mcfw.exceptions import HttpBadRequestException, HttpForbiddenException
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.service import re_index_map_only
from rogerthat.consts import FAST_QUEUE
from rogerthat.models import ServiceIdentity
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.rpc.users import get_current_session
from rogerthat.utils.service import create_service_identity_user
from shop.dal import get_customer
from shop.models import Customer
from solutions import translate
from solutions.common.bizz import SolutionModule
from solutions.common.bizz.campaignmonitor import send_smart_email_without_check
from solutions.common.dal import get_solution_settings
from solutions.common.integrations.cirklo.cirklo import get_city_id_by_service_email, whitelist_merchant, \
    list_whitelisted_merchants
from solutions.common.integrations.cirklo.models import CirkloCity, CirkloMerchant, SignupNames, SignupMails
from solutions.common.integrations.cirklo.to import CirkloCityTO, CirkloVoucherListTO, CirkloVoucherServiceTO, \
    WhitelistVoucherServiceTO
from solutions.common.restapi.services import _check_is_city


def _check_permission(city_sln_settings):
    if SolutionModule.CIRKLO_VOUCHERS not in city_sln_settings.modules:
        raise HttpForbiddenException()

    if len(city_sln_settings.modules) != 1:
        city_customer = get_customer(city_sln_settings.service_user)
        _check_is_city(city_sln_settings, city_customer)


@rest('/common/vouchers/services', 'get', silent_result=True)
@returns(CirkloVoucherListTO)
@arguments()
def get_cirklo_vouchers_services():
    city_service_user = users.get_current_user()
    city_sln_settings = get_solution_settings(city_service_user)
    _check_permission(city_sln_settings)

    to = CirkloVoucherListTO()
    to.total = 0
    to.results = []
    to.cursor = None
    to.more = False

    cirklo_city = CirkloCity.get_by_service_email(city_service_user.email())
    if not cirklo_city:
        return to

    cirklo_merchants = list_whitelisted_merchants(cirklo_city.city_id)
    cirklo_dict = {}
    cirklo_emails = []
    for m in cirklo_merchants:
        if m['email'] in cirklo_emails:
            logging.error('Duplicate found %s', m['email'])
            continue
        cirklo_emails.append(m['email'])
        cirklo_dict[m['email']] = m

    qry = CirkloMerchant.list_by_city_id(cirklo_city.city_id)
    osa_merchants = []
    for m in qry:
        if m.service_user_email:
            osa_merchants.append(m)
        else:
            cirklo_merchant = cirklo_dict.get(m.data['company']['email'])
            if cirklo_merchant:
                if m.data['company']['email'] in cirklo_emails:
                    cirklo_emails.remove(m.data['company']['email'])
                if not m.whitelisted:
                    m.whitelisted = True
                    m.put()
            elif m.whitelisted:
                m.whitelisted = False
                m.put()

            whitelist_date = cirklo_merchant['createdAt'] if cirklo_merchant else None
            merchant_registered = 'shopInfo' in cirklo_merchant if cirklo_merchant else False
            to.results.append(CirkloVoucherServiceTO.from_model(m, whitelist_date, merchant_registered, u'Cirklo signup'))

    if osa_merchants:
        customer_to_get = [m.customer_id for m in osa_merchants]
        customers_dict = {}
        for c in Customer.get_by_id(customer_to_get):
            customers_dict[c.id] = c
        info_keys = [ServiceInfo.create_key(users.User(m.service_user_email), ServiceIdentity.DEFAULT) for m in osa_merchants]
        models = ndb.get_multi(info_keys)

        for service_info, m in zip(models, osa_merchants):
            customer = customers_dict[m.customer_id]
            cirklo_merchant = cirklo_dict.get(customer.user_email)
            should_save = False
            if cirklo_merchant:
                if customer.user_email in cirklo_emails:
                    cirklo_emails.remove(customer.user_email)
                if not m.whitelisted:
                    m.whitelisted = True
                    should_save = True
            elif m.whitelisted:
                m.whitelisted = False
                should_save = True

            if should_save:
                m.put()
                service_identity_user = create_service_identity_user(customer.service_user)
                deferred.defer(re_index_map_only, service_identity_user)

            whitelist_date = cirklo_merchant['createdAt'] if cirklo_merchant else None
            merchant_registered = 'shopInfo' in cirklo_merchant if cirklo_merchant else False
            service_to = CirkloVoucherServiceTO.from_model(m, whitelist_date,  merchant_registered, u'OSA signup')
            service_to.populate_from_info(service_info, customer)
            to.results.append(service_to)

    for email in cirklo_emails:
        cirklo_merchant = cirklo_dict[email]
        to.results.append(CirkloVoucherServiceTO.from_cirklo_info(cirklo_merchant))
    return to


@rest('/common/vouchers/services/whitelist', 'put', type=REST_TYPE_TO)
@returns(CirkloVoucherServiceTO)
@arguments(data=WhitelistVoucherServiceTO)
def whitelist_voucher_service(data):
    city_service_user = users.get_current_user()
    city_sln_settings = get_solution_settings(city_service_user)
    _check_permission(city_sln_settings)

    cirklo_city = CirkloCity.get_by_service_email(city_service_user.email())
    if not cirklo_city:
        raise HttpBadRequestException()

    if not (cirklo_city.signup_mails and cirklo_city.signup_mails.accepted and cirklo_city.signup_mails.denied):
        raise HttpBadRequestException('City settings aren\'t fully setup yet.')

    if data.accepted:
        whitelist_merchant(cirklo_city.city_id, data.email)
        deferred.defer(send_smart_email_without_check, cirklo_city.signup_mails.accepted, [data.email], _countdown=1, _queue=FAST_QUEUE)
    else:
        deferred.defer(send_smart_email_without_check, cirklo_city.signup_mails.denied, [data.email], _countdown=1, _queue=FAST_QUEUE)

    if data.id:
        whitelist_date = datetime.now().isoformat() + 'Z' if data.accepted else None
        if '@' in data.id:
            m = CirkloMerchant.create_key(data.id).get()
            if data.accepted:
                m.whitelisted = True
            else:
                m.denied = True
            m.put()

            service_info = ServiceInfo.create_key(users.User(m.service_user_email), ServiceIdentity.DEFAULT).get()
            customer = Customer.get_by_id(m.customer_id)  # type: Customer

            if data.accepted:
                service_identity_user = create_service_identity_user(customer.service_user)
                deferred.defer(re_index_map_only, service_identity_user)
            to = CirkloVoucherServiceTO.from_model(m, whitelist_date, False, u'OSA signup')
            to.populate_from_info(service_info, customer)
            return to
        else:
            m = CirkloMerchant.get_by_id(long(data.id))
            if data.accepted:
                m.whitelisted = True
            else:
                m.denied = True
            m.put()

            return CirkloVoucherServiceTO.from_model(m, whitelist_date, False, u'Cirklo signup')


@rest('/common/vouchers/cirklo', 'get')
@returns(CirkloCityTO)
@arguments()
def api_vouchers_get_cirklo_settings():
    service_user = users.get_current_user()
    city = CirkloCity.get_by_service_email(service_user.email())
    return CirkloCityTO.from_model(city)


@rest('/common/vouchers/cirklo', 'put')
@returns(CirkloCityTO)
@arguments(data=CirkloCityTO)
def api_vouchers_save_cirklo_settings(data):
    service_user = users.get_current_user()
    if not get_current_session().shop:
        lang = get_solution_settings(service_user).main_language
        raise HttpForbiddenException(translate(lang, 'no_permission'))
    other_city = CirkloCity.get_by_service_email(service_user.email())  # type: CirkloCity
    if not data.city_id:
        if other_city:
            other_city.key.delete()
        return CirkloCityTO.from_model(None)

    key = CirkloCity.create_key(data.city_id)
    city = key.get()
    if not city:
        city = CirkloCity(key=key, service_user_email=service_user.email())
    elif city.service_user_email != service_user.email():
        raise HttpBadRequestException('City id %s is already in use by another service' % data.city_id)
    if other_city and other_city.key != key:
        other_city.key.delete()
    invalidate_cache(get_city_id_by_service_email, service_user.email())
    city.logo_url = data.logo_url
    city.signup_enabled = False
    city.signup_logo_url = data.signup_logo_url
    city.signup_mails = None
    city.signup_names = None

    if data.signup_mail_id_accepted and data.signup_mail_id_denied:
        city.signup_mails = SignupMails(accepted=data.signup_mail_id_accepted,
                                        denied=data.signup_mail_id_denied)

    if data.signup_name_nl and data.signup_name_fr:
        city.signup_enabled = True
        city.signup_names = SignupNames(nl=data.signup_name_nl,
                                        fr=data.signup_name_fr)
    elif data.signup_name_nl:
        city.signup_enabled = True
        city.signup_names = SignupNames(nl=data.signup_name_nl,
                                        fr=data.signup_name_nl)
    elif data.signup_name_fr:
        city.signup_enabled = True
        city.signup_names = SignupNames(nl=data.signup_name_fr,
                                        fr=data.signup_name_fr)

    city.put()
    return CirkloCityTO.from_model(city)
