# -*- coding: utf-8 -*-
# Copyright 2021 Green Valley NV
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
from __future__ import unicode_literals

import json

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from requests import sessions, Response
from typing import List, Optional

from mcfw.utils import Enum
from rogerthat.consts import DEBUG
from rogerthat.rpc import users
from rogerthat.to import convert_to_unicode, TO
from rogerthat.to.service import UserDetailsTO, SendApiCallCallbackResultTO
from solutions import translate
from solutions.common.dal import get_solution_settings
from solutions.common.integrations.timeblockr.models import TimeblockrSettings


class TimeblockrApiMethod(Enum):
    GET_APPOINTMENTS = 'integrations.timeblockr.get_appointments'
    GET_PRODUCTS = 'integrations.timeblockr.get_products'
    GET_LOCATIONS = 'integrations.timeblockr.get_locations'
    GET_TIMESLOTS = 'integrations.timeblockr.get_timeslots'
    GET_DYNAMIC_FIELDS = 'integrations.timeblockr.get_dynamic_fields'
    BOOK_APPOINTMENT = 'integrations.timeblockr.book_appointment'


def product_to_url_string(product):
    return '%s;%s' % (product['id'], product['amount'])


def get_appointments(settings, app_user):
    # TODO: not sure if even possible
    return []


def get_products(settings, selected_products=None):
    # type: (TimeblockrSettings, Optional[List[str]]) -> object
    if not selected_products:
        return timeblockr_request(settings, '/v2/products')
    else:
        product_filter = ','.join(product_to_url_string(p) for p in selected_products)
        return timeblockr_request(settings, '/v2/products/productfilter/%s' % product_filter)


def get_locations(settings):
    return timeblockr_request(settings, '/v2/locations')


def get_timeslots(settings, selected_products, location_id, selected_date=None):
    # type: (TimeblockrSettings, List[dict], str, str) -> Response
    if selected_date:
        # Fetch timeslots for a specific day. 'SlotOptions' will contain hours.
        params = {
            'mode': 'firstavailable',
            'firstavailabletop': 100,
            'slotOptionResourceItems': True,
        }
        start_date = selected_date
        end_date = selected_date
    else:
        # Fetch all days with available timeslots. 'SlotOptions' will not contain hours.
        params = {'mode': 'possibility'}
        start_date = datetime.now().date().isoformat()
        end_date = (datetime.now().date() + relativedelta(months=2))
    # Not actually sure if this is the way, not documented
    product_str = ','.join(product_to_url_string(p) for p in selected_products)
    url = '/v2/timeslots/{product_str}/{location_id}/{start_date}/{end_date}'.format(product_str=product_str,
                                                                                     location_id=location_id,
                                                                                     start_date=start_date,
                                                                                     end_date=end_date)
    result = timeblockr_request(settings, url, params=params)
    result_json = result.json()
    # Simplify return data as we don't need all the junk it contains
    if selected_date:
        return [{'date': slot_option['Date']} for slot_option in result_json['SlotOptions']]
    else:
        return [{'date': period_option['Date']} for period_option in result_json['PeriodOptions']]


def get_dynamic_fields(settings, selected_products, location_id):
    params = {
        # again, not sure if correct
        'productUnits': [product_to_url_string(product) for product in selected_products],
        'locations': location_id,
    }

    return timeblockr_request(settings, '/v2/dynamicfields', params=params)


def book_appointment(settings, data):
    return timeblockr_request(settings, '/v2/bookings', 'POST', payload=data)


def timeblockr_request(settings, relative_url, method='GET', params=None, payload=None):
    # type: (TimeblockrSettings, unicode, unicode, Optional[dict], Optional[dict]) -> Response
    url = '%s%s' % (settings.url, relative_url)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'API-Key ': settings.api_key
    }
    logging.debug('%s %s', method, url)

    with sessions.Session() as session:
        result = session.request(method, url, params=params, json=payload, headers=headers, timeout=15,
                                 allow_redirects=False)
        result.raise_for_status()
    if DEBUG:
        logging.debug(result.content)
    return result


def handle_method(service_user, email, method, params, tag, service_identity, user_details):
    # type: (users.User, str, str, str, str, str, List[UserDetailsTO]) -> SendApiCallCallbackResultTO
    response = SendApiCallCallbackResultTO()
    settings = TimeblockrSettings.create_key(service_user).get()  # type: TimeblockrSettings
    if not settings:
        raise Exception('Timeblockr settings not set for %s' % service_user)
    try:
        json_data = json.loads(params) if params else {}
        user = user_details[0]
        app_user = user.toAppUser()
        if method == TimeblockrApiMethod.GET_APPOINTMENTS:
            result = get_appointments(settings, app_user)
        if method == TimeblockrApiMethod.GET_PRODUCTS:
            result = get_products(settings, json_data.get('selectedProducts', []))
        if method == TimeblockrApiMethod.GET_LOCATIONS:
            result = get_locations(settings)
        elif method == TimeblockrApiMethod.GET_TIMESLOTS:
            result = get_timeslots(settings, json_data['selectedProducts'], json_data['locationId'],
                                   json_data.get('selectedDate'))
        elif method == TimeblockrApiMethod.GET_DYNAMIC_FIELDS:
            result = get_dynamic_fields(settings, json_data['selectedProducts'], json_data['locationId'])
        elif method == TimeblockrApiMethod.BOOK_APPOINTMENT:
            result = book_appointment(settings, json_data)
        else:
            raise NotImplementedError('Method %s not implemented' % method)

        if isinstance(result, Response):
            response.result = result.content
            response.error = None
            return response
        response.result = convert_to_unicode(json.dumps(result.to_dict() if isinstance(result, TO) else result))
    except Exception:
        logging.error('Error while handling timeblockr call %s' % method, exc_info=True)
        sln_settings = get_solution_settings(service_user)
        response.error = translate(sln_settings.main_language, 'error-occured-unknown')
    return response
