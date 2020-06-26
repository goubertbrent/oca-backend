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

import csv
from datetime import datetime
import logging
import urllib

from babel.dates import format_datetime
import cloudstorage
from google.appengine.ext import ndb, db
from google.appengine.ext.deferred import deferred
from typing import List

from mcfw.cache import invalidate_cache
from mcfw.consts import REST_TYPE_TO
from mcfw.exceptions import HttpBadRequestException, HttpForbiddenException
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.bizz.service import re_index_map_only
from rogerthat.consts import FILES_BUCKET, SCHEDULED_QUEUE, DAY
from rogerthat.models import ServiceIdentity
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.rpc.users import get_current_session
from rogerthat.translations import localize
from rogerthat.utils import try_or_defer
from rogerthat.utils.service import create_service_identity_user
from shop.dal import get_customer
from shop.models import Customer
from solutions import translate
from solutions.common.bizz import OrganizationType
from solutions.common.dal import get_solution_settings
from solutions.common.integrations.cirklo.cirklo import get_city_id_by_service_email
from solutions.common.integrations.cirklo.models import VoucherSettings, VoucherProviderId, CirkloCity
from solutions.common.integrations.cirklo.to import VoucherListTO, VoucherServiceTO, UpdateVoucherServiceTO,\
    CirkloCityTO
from solutions.common.models import SolutionServiceConsent
from solutions.common.restapi.services import _check_is_city


@rest('/common/vouchers/services/<organization_type:\d>', 'get', silent_result=True)
@returns(VoucherListTO)
@arguments(organization_type=(int, long), sort=unicode, cursor=unicode, page_size=(int, long))
def get_vouchers_services(organization_type, sort=None, cursor=None, page_size=50):
    city_service_user = users.get_current_user()
    city_sln_settings = get_solution_settings(city_service_user)
    city_customer = get_customer(city_service_user)
    _check_is_city(city_sln_settings, city_customer)
    if sort == 'name':
        service_customers_qry = Customer.list_enabled_by_organization_type_in_app(city_customer.app_id,
                                                                                  organization_type)
    else:
        service_customers_qry = Customer.list_enabled_by_organization_type_in_app_by_creation_time(city_customer.app_id,
                                                                                                   organization_type)
    service_customers_qry.with_cursor(cursor)
    customers = [c for c in service_customers_qry.fetch(page_size) if c.service_email]
    keys = [VoucherSettings.create_key(customer.service_user) for customer in customers] + [
        SolutionServiceConsent.create_key(customer.user_email) for customer in customers]
    models = ndb.get_multi(keys)
    all_voucher_settings = models[:len(models) / 2]
    service_consents = models[len(models) / 2:]
    to = VoucherListTO()
    to.total = Customer.list_enabled_by_organization_type_in_app(city_customer.app_id, organization_type).count()
    to.results = [VoucherServiceTO.from_models(customer, voucher_settings, consent)
                  for customer, voucher_settings, consent in zip(customers, all_voucher_settings, service_consents)]
    to.cursor = unicode(service_customers_qry.cursor())
    to.more = len(to.results) > 0
    return to


@rest('/common/vouchers/services/<service_email:[^/]+>', 'put', type=REST_TYPE_TO)
@returns(VoucherServiceTO)
@arguments(service_email=unicode, data=UpdateVoucherServiceTO)
def save_voucher_settings(service_email, data):
    # type: (unicode, UpdateVoucherServiceTO) -> List[VoucherServiceTO]
    city_service_user = users.get_current_user()
    city_sln_settings = get_solution_settings(city_service_user)
    city_customer = get_customer(city_service_user)
    _check_is_city(city_sln_settings, city_customer)

    customer = get_customer(users.User(service_email))
    settings_key = VoucherSettings.create_key(users.User(service_email))
    settings, service_consent = ndb.get_multi([settings_key, SolutionServiceConsent.create_key(
        customer.user_email)])  # type: VoucherSettings, SolutionServiceConsent
    if service_consent and VoucherProviderId.CIRKLO in data.providers \
        and SolutionServiceConsent.TYPE_CIRKLO_SHARE not in service_consent.types:
        err = translate(customer.language, 'oca.cirklo_disabled_reason_privacy')
        raise HttpBadRequestException(err)
    if not settings:
        settings = VoucherSettings(key=settings_key)  # type: VoucherSettings
    settings.customer_id = customer.id
    settings.app_id = city_customer.app_id
    settings.providers = data.providers
    settings.put()
    service_identity_user = create_service_identity_user(customer.service_user)
    try_or_defer(re_index_map_only, service_identity_user)
    return VoucherServiceTO.from_models(customer, settings, service_consent)


@rest('/common/vouchers/export', 'get')
@returns(dict)
@arguments()
def export_voucher_services():
    # type: () -> dict
    city_service_user = users.get_current_user()
    city_sln_settings = get_solution_settings(city_service_user)
    city_customer = get_customer(city_service_user)
    _check_is_city(city_sln_settings, city_customer)

    qry = VoucherSettings.list_by_provider_and_app(VoucherProviderId.CIRKLO, city_customer.app_id)
    voucher_settings = qry.fetch(None)  # type: List[VoucherSettings]
    customers = db.get(
        [Customer.create_key(settings.customer_id) for settings in voucher_settings])  # type: List[Customer]
    service_infos = ndb.get_multi([ServiceInfo.create_key(s.service_user, ServiceIdentity.DEFAULT)
                                   for s in voucher_settings])  # type: List[ServiceInfo]
    date = format_datetime(datetime.now(), locale='en_GB', format='medium').replace(' ', '-')
    filename = 'vouchers-%s-%s.csv' % (city_customer.name, date)
    gcs_path = '/%s/services/%s/export/%s' % (FILES_BUCKET, city_service_user.email(), filename)
    org_types = {org_type: localize('en', key) for org_type, key in OrganizationType.get_translation_keys().iteritems()}
    with cloudstorage.open(gcs_path, 'w', content_type='text/csv') as gcs_file:
        field_names = ['Name', 'Login email', 'Phone number', 'Date created', 'Organization type', 'Street',
                       'Street number', 'Postal code', 'Place', 'Location url']
        writer = csv.DictWriter(gcs_file, dialect='excel', fieldnames=field_names)
        writer.writeheader()
        rows = []
        missing = []
        for voucher_setting, customer, service_info in zip(voucher_settings, customers, service_infos):
            if not customer or not service_info:
                missing.append((voucher_setting.service_user.email(),
                                'Customer: %s' % (customer is None),
                                'ServiceInfo: %s' % (service_info is None)))
                continue
            row = {
                'Login email': customer.user_email,
                'Name': service_info.name.encode('utf8') if service_info.name else '',
                'Phone number': service_info.main_phone_number,
                'Date created': datetime.utcfromtimestamp(customer.creation_time),
                'Organization type': org_types[customer.organization_type]
            }
            address = service_info.addresses[0] if service_info.addresses else None
            if address:
                row['Street'] = address.street.encode('utf8')
                row['Street number'] = address.street_number
                row['Postal code'] = address.postal_code
                row['Place'] = address.locality.encode('utf8')
                params = {'api': '1', 'query': address.name or address.get_address_line(customer.locale)}
                if address.google_maps_place_id:
                    params['query_place_id'] = address.google_maps_place_id
                row['Location url'] = 'https://www.google.com/maps/search/?%s' % urllib.urlencode(params, doseq=True)
            logging.debug(row)
            rows.append(row)
        if missing:
            logging.error('Some data was missing when exporting services: %s', missing)
        sorted_rows = sorted(rows, key=lambda row: row['Name'])
        writer.writerows(sorted_rows)

    deferred.defer(cloudstorage.delete, gcs_path, _countdown=DAY, _queue=SCHEDULED_QUEUE)
    return {'url': get_serving_url(gcs_path), 'filename': filename}


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
    city.put()
    return CirkloCityTO.from_model(city)
