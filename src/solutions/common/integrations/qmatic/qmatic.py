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
from __future__ import unicode_literals

import hashlib
import json
import logging
import uuid
from datetime import datetime

from google.appengine.api import urlfetch
from google.appengine.ext.deferred import deferred

import cloudstorage
import dateutil
from icalendar import Calendar, Event, vCalAddress, vText
from mcfw.exceptions import HttpBadRequestException
from mcfw.rpc import returns, arguments
from models import QMaticSettings, QMaticUser
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.consts import DEBUG
from rogerthat.rpc import users
from rogerthat.to.service import SendApiCallCallbackResultTO, UserDetailsTO
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import broadcast_updates_pending
from solutions.common.consts import OCA_FILES_BUCKET
from solutions.common.dal import get_solution_settings

API_METHOD_APPOINTMENTS = 'integrations.qmatic.appointments'
API_METHOD_SERVICES = 'integrations.qmatic.services'
API_METHOD_BRANCHES = 'integrations.qmatic.branches'
API_METHOD_DATES = 'integrations.qmatic.dates'
API_METHOD_TIMES = 'integrations.qmatic.times'
API_METHOD_RESERVE = 'integrations.qmatic.reserve'
API_METHOD_CONFIRM = 'integrations.qmatic.confirm'
API_METHOD_DELETE = 'integrations.qmatic.delete'
API_METHOD_CREATE_ICAL = 'integrations.qmatic.create_ical'

URL_PREFIX = '/calendar-backend/public/api/v1'


class TranslatedException(Exception):

    def __init__(self, translation_key, params=None):
        self.translation_key = translation_key
        self.params = params or {}

    def get_message(self, language):
        return common_translate(language, SOLUTION_COMMON, self.translation_key, **self.params)


def get_qmatic_settings(service_user):
    # type: (users.User) -> QMaticSettings
    key = QMaticSettings.create_key(service_user)
    settings = key.get()
    if not settings:
        settings = QMaticSettings(key=key, url=None, auth_token=None)
    return settings


def set_updates_pending(service_user):
    sln_settings = get_solution_settings(service_user)
    sln_settings.updates_pending = True
    sln_settings.put()
    broadcast_updates_pending(sln_settings)


def save_qmatic_settings(service_user, url, auth_token):
    settings = get_qmatic_settings(service_user)
    settings.url = url.strip()
    settings.auth_token = auth_token.strip()
    try:
        if url and auth_token:
            if get_services(settings).status_code == 200:
                if not settings.enabled:
                    settings.enabled = True
                    set_updates_pending(service_user)
                settings.put()
            else:
                raise HttpBadRequestException('errors.invalid_qmatic_credentials')
        else:
            if settings.enabled:
                settings.enabled = False
                set_updates_pending(service_user)
            settings.put()
    except urlfetch.Error as e:
        raise HttpBadRequestException(e.message)
    return settings


def do_request(settings, relative_url, method=urlfetch.GET, payload=None):
    # type: (QMaticSettings, str, int, dict) -> urlfetch._URLFetchResult
    url = '%s%s' % (settings.url, relative_url)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'auth-token': settings.auth_token
    }
    if payload:
        payload = json.dumps(payload)
    else:
        payload = None
    if DEBUG:
        logging.debug(url)
    result = urlfetch.fetch(url, payload, method, headers, deadline=30, follow_redirects=False)
    if DEBUG:
        logging.debug(result.content)
    return result


def get_user_hash(app_user):
    return hashlib.sha256(app_user.email()).hexdigest().upper()


@returns(SendApiCallCallbackResultTO)
@arguments(service_user=users.User, email=unicode, method=unicode, params=unicode, tag=unicode, service_identity=unicode,
           user_details=[UserDetailsTO])
def handle_method(service_user, email, method, params, tag, service_identity, user_details):
    # type: (users.User, str, str, str, str, str, list[UserDetailsTO]) -> SendApiCallCallbackResultTO
    response = SendApiCallCallbackResultTO()
    try:
        app_user = user_details[0].toAppUser()
        settings = QMaticSettings.create_key(service_user).get()
        if not settings:
            raise Exception('Qmatic settings not found')

        jsondata = json.loads(params) if params else None
        if API_METHOD_APPOINTMENTS == method:
            result = get_appointments(settings, app_user)
        elif API_METHOD_SERVICES == method:
            result = get_services(settings)
        elif API_METHOD_BRANCHES == method:
            result = get_branches(settings, **jsondata)
        elif API_METHOD_DATES == method:
            result = get_dates(settings, **jsondata)
        elif API_METHOD_TIMES == method:
            result = get_times(settings, **jsondata)
        elif API_METHOD_RESERVE == method:
            result = reserve_date(settings, **jsondata)
        elif API_METHOD_CONFIRM == method:
            result = confirm_reservation(settings, app_user, jsondata.pop('reservation_id'), jsondata)
        elif API_METHOD_DELETE == method:
            result = delete_appointment(settings, app_user, **jsondata)
        elif API_METHOD_CREATE_ICAL == method:
            result = create_ical(settings, **jsondata)
        else:
            raise Exception('Qmatic method not found')

        if isinstance(result, urlfetch._URLFetchResult):
            if result.status_code in (200, 204):
                response.result = result.content.decode('utf-8')
                response.error = None
                return response
            else:
                logging.debug('%s: %s', result.status_code, result.content)
                raise Exception('Error returned from Q-Matic')
        else:
            response.result = (json.dumps(result) if isinstance(result, dict) else result).decode('utf-8')
    except TranslatedException as e:
        response.error = e.get_message(get_solution_settings(service_user).main_language)
    except Exception:
        logging.error('Error while handling q-matic call %s' % method, exc_info=True)
        sln_settings = get_solution_settings(service_user)
        response.error = common_translate(sln_settings.main_language, SOLUTION_COMMON, 'error-occured-unknown')
    return response


def get_appointments(qmatic_settings, app_user):
    # type: (QMaticSettings, users.User) -> urlfetch._URLFetchResult
    qmatic_user = QMaticUser.create_key(app_user).get()
    if not qmatic_user:
        return {
            'meta': {
                'start': '',
                'end': '',
                'totalResults': 0,
                'offset': None,
                'limit': None,
                'fields': '',
                'arguments': {}
            },
            'appointmentList': [],
            'notifications': [],
        }
    url = '%s/customers/externalId/%s/appointments' % (URL_PREFIX, qmatic_user.qmatic_id)
    return do_request(qmatic_settings, url)


def get_services(qmatic_settings):
    # type: (QMaticSettings) -> urlfetch._URLFetchResult
    url = '%s/services' % URL_PREFIX
    return do_request(qmatic_settings, url)


def get_branches(qmatic_settings, service_id):
    # type: (QMaticSettings, str) -> urlfetch._URLFetchResult
    url = '%s/services/%s/branches' % (URL_PREFIX, service_id)
    return do_request(qmatic_settings, url)


def get_dates(qmatic_settings, service_id, branch_id):
    # type: (QMaticSettings, str, str) -> urlfetch._URLFetchResult
    url = '%s/branches/%s/services/%s/dates' % (URL_PREFIX, branch_id, service_id)
    return do_request(qmatic_settings, url)


def get_times(qmatic_settings, service_id, branch_id, date):
    # type: (QMaticSettings, str, str, str) -> urlfetch._URLFetchResult
    url = '%s/branches/%s/services/%s/dates/%s/times' % (URL_PREFIX, branch_id, service_id, date)
    return do_request(qmatic_settings, url)


def reserve_date(qmatic_settings, service_id, branch_id, date, time):
    # type: (QMaticSettings, str, str, str, str) -> urlfetch._URLFetchResult
    url = '%s/branches/%s/services/%s/dates/%s/times/%s/reserve' % (URL_PREFIX, branch_id, service_id, date, time)
    return do_request(qmatic_settings, url, urlfetch.POST)


def confirm_reservation(qmatic_settings, app_user, reservation_id, data):
    # type: (QMaticSettings, users.User, str, dict) -> urlfetch._URLFetchResult
    url = '%s/branches/appointments/%s/confirm' % (URL_PREFIX, reservation_id)
    user_key = QMaticUser.create_key(app_user)
    qmatic_user = user_key.get()
    if not qmatic_user:
        qmatic_user = QMaticUser(key=user_key)
        qmatic_user.qmatic_id = str(uuid.uuid4())
        qmatic_user.put()
    data['customer']['externalId'] = qmatic_user.qmatic_id
    return do_request(qmatic_settings, url, urlfetch.POST, data)


def delete_appointment(qmatic_settings, app_user, appointment_id):
    # type: (QMaticSettings, users.User, str) -> urlfetch._URLFetchResult
    url = '%s/appointments/%s' % (URL_PREFIX, appointment_id)
    qmatic_user = _get_qmatic_user(app_user)
    result = get_appointment(qmatic_settings, appointment_id)
    try:
        appointment = json.loads(result.content)
    except Exception as e:
        logging.warning(e, exc_info=True)
        return result
    can_delete = any(customer['externalId'] == qmatic_user.qmatic_id
                     for customer in appointment['appointment']['customers'])
    if not can_delete:
        logging.warning('%s tried to delete appointment to which he has no access: %s', app_user, appointment_id)
        raise TranslatedException('no_permission_to_appointment')
    else:
        return do_request(qmatic_settings, url, urlfetch.DELETE)


def get_appointment(qmatic_settings, appointment_id):
    url = '%s/appointments/%s' % (URL_PREFIX, appointment_id)
    return do_request(qmatic_settings, url)


def create_ical(qmatic_settings, appointment_id):
    result = get_appointment(qmatic_settings, appointment_id)
    if result.status_code != 200:
        return result
    appointment = json.loads(result.content)['appointment']
    cal = Calendar()
    cal.add('prodid', '-//Our City App//calendar//')
    cal.add('version', '2.0')
    cal.add('CALSCALE', 'GREGORIAN')
    cal.add('method', 'REQUEST')
    event = Event()
    event.add('uid', appointment_id)
    event.add('summary', appointment['title'])
    event.add('description', appointment['notes'] or '')
    location = ''
    if appointment['branch']:
        parts = [
            appointment['branch']['addressLine1'],
            appointment['branch']['addressLine2'],
            ('%s %s' % (appointment['branch']['addressZip'] or '', appointment['branch']['addressCity'] or '')).strip(),
            appointment['branch']['addressCountry']
        ]
        location = ', '.join(p for p in parts if p)
    organizer_email = None
    organizer_name = None
    if appointment['customers']:
        customer = appointment['customers'][0]
        organizer_email = customer['email']
        organizer_name = customer['name']
    event.add('location', location)
    event.add('dtstart', dateutil.parser.parse(appointment['start']))
    event.add('dtend', dateutil.parser.parse(appointment['end']))
    event.add('dtstamp', datetime.utcnow())
    event.add('created', datetime.utcfromtimestamp(appointment['created'] / 1000))
    event.add('updated', datetime.utcfromtimestamp(appointment['updated'] / 1000))
    organizer = vCalAddress('MAILTO:%s' % organizer_email)
    organizer.params['cn'] = vText(organizer_name)
    event.add('organizer', organizer)
    cal.add_component(event)
    path = '/%s/tmp/q-matic/%s.ics' % (OCA_FILES_BUCKET, appointment_id)
    with cloudstorage.open(path, 'w', 'text/calendar') as f:
        f.write(cal.to_ical())
    url = get_serving_url(path)
    deferred.defer(_delete_file, path, _countdown=60)
    file_name = '%s.ics' % appointment['title']
    return {'url': url, 'file_name': file_name}


def _get_qmatic_user(app_user):
    # type: (users.User) -> QMaticUser
    user_key = QMaticUser.create_key(app_user)
    qmatic_user = user_key.get()
    if not qmatic_user:
        qmatic_user = QMaticUser(key=user_key)
        qmatic_user.qmatic_id = str(uuid.uuid4())
        qmatic_user.put()
    return qmatic_user


def _delete_file(path):
    try:
        cloudstorage.delete(path)
    except cloudstorage.NotFoundError:
        pass