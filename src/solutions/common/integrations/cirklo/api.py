# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
import csv
import logging
import urllib
from datetime import datetime

import cloudstorage
from babel.dates import format_datetime
from google.appengine.ext import ndb, db
from google.appengine.ext.deferred import deferred
from typing import List

from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.consts import FILES_BUCKET, SCHEDULED_QUEUE, DAY
from rogerthat.models import ServiceIdentity
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.translations import localize
from shop.dal import get_customer
from shop.models import Customer
from solutions.common.bizz import OrganizationType
from solutions.common.dal import get_solution_settings
from solutions.common.integrations.cirklo.models import VoucherSettings, VoucherProviderId
from solutions.common.integrations.cirklo.to import VoucherListTO, VoucherServiceTO, UpdateVoucherServiceTO
from solutions.common.restapi.services import _check_is_city


@rest('/common/vouchers/services/<organization_type:\d>', 'get', silent_result=True)
@returns(VoucherListTO)
@arguments(organization_type=(int, long), cursor=unicode, page_size=(int, long))
def get_vouchers_services(organization_type, cursor=None, page_size=50):
    city_service_user = users.get_current_user()
    city_sln_settings = get_solution_settings(city_service_user)
    city_customer = get_customer(city_service_user)
    _check_is_city(city_sln_settings, city_customer)
    service_customers_qry = Customer.list_enabled_by_organization_type_in_app(city_customer.app_id, organization_type)
    service_customers_qry.with_cursor(cursor)
    customers = [c for c in service_customers_qry.fetch(page_size) if c.service_email]
    keys = [VoucherSettings.create_key(customer.service_user) for customer in customers]
    models = ndb.get_multi(keys)
    to = VoucherListTO()
    to.total = Customer.list_enabled_by_organization_type_in_app(city_customer.app_id, organization_type).count()
    to.results = [VoucherServiceTO.from_models(customer, voucher_settings)
                  for customer, voucher_settings in zip(customers, models)]
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

    customer = Customer.get_by_service_email(service_email)
    settings_key = VoucherSettings.create_key(users.User(service_email))
    settings = settings_key.get() or VoucherSettings(key=settings_key)  # type: VoucherSettings
    settings.customer_id = customer.id
    settings.app_id = city_customer.app_id
    settings.providers = data.providers
    settings.put()
    return VoucherServiceTO.from_models(customer, settings)


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
                'Name': service_info.name,
                'Phone number': service_info.main_phone_number,
                'Date created': datetime.utcfromtimestamp(customer.creation_time),
                'Organization type': org_types[customer.organization_type]
            }
            address = service_info.addresses[0] if service_info.addresses else None
            if address:
                row['Street'] = address.street
                row['Street number'] = address.street_number
                row['Postal code'] = address.postal_code
                row['Place'] = address.locality
                params = {'api': '1', 'query': address.name or address.get_address_line(customer.locale)}
                if address.google_maps_place_id:
                    params['query_place_id'] = address.google_maps_place_id
                row['Location url'] = 'https://www.google.com/maps/search/?%s' % urllib.urlencode(params, doseq=True)
            rows.append(row)
        if missing:
            logging.error('Some data was missing when exporting services: %s', missing)
        writer.writerows(sorted(rows, key=lambda row: row['Name']))

    deferred.defer(cloudstorage.delete, gcs_path, _countdown=DAY, _queue=SCHEDULED_QUEUE)
    return {'url': get_serving_url(gcs_path), 'filename': filename}
