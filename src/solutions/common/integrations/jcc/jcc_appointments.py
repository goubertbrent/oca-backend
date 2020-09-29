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

import json
import logging
from base64 import b64encode
from datetime import datetime, date

import zeep
from babel.dates import format_time, format_date
from functools32 import lru_cache
from google.appengine.ext import deferred, ndb
from icalendar import Calendar, Event, vCalAddress, vText
from requests import Session
from requests.auth import HTTPBasicAuth
from typing import List, Dict
from zeep import Client, Transport
from zeep.helpers import serialize_object
from zeep.xsd import CompoundValue, Schema

from mcfw.cache import cached
from mcfw.exceptions import HttpBadRequestException
from mcfw.rpc import returns, arguments
from rogerthat.bizz.app import get_app
from rogerthat.consts import DAY
from rogerthat.rpc import users
from rogerthat.to import convert_to_unicode
from rogerthat.to.service import SendApiCallCallbackResultTO, UserDetailsTO
from rogerthat.utils import send_mail
from rogerthat.utils.app import get_human_user_from_app_user, get_app_id_from_app_user
from solutions import translate
from solutions.common.dal import get_solution_settings
from solutions.common.integrations.jcc.models import JCCSettings, JccApiMethod, JCCUserAppointments, JCCAppointment
from solutions.common.integrations.qmatic.qmatic import set_updates_pending

# Disable logging of discovery of methods and types
logging.getLogger('zeep.wsdl.wsdl').setLevel(logging.INFO)
logging.getLogger('zeep.xsd.schema').setLevel(logging.INFO)


@lru_cache()
def get_jcc_client(url, username, password):
    session = Session()
    if username and password:
        session.auth = HTTPBasicAuth(username, password)
        transport = Transport(session=session)
    else:
        transport = Transport()
    transport.operation_timeout = 30
    return Client(url, transport=transport)


def get_jcc_settings(service_user):
    # type: (users.User) -> JCCSettings
    key = JCCSettings.create_key(service_user)
    settings = key.get()
    if not settings:
        settings = JCCSettings(key=key, url=None)
    return settings


def save_jcc_settings(service_user, url, username=None, password=None):
    # type: (users.User, str, str, str) -> JCCSettings
    settings = get_jcc_settings(service_user)
    settings.url = url
    settings.username = username
    settings.password = password
    if url:
        try:
            client = get_jcc_client(settings.url, settings.username, settings.password)
            client.service.getGovAvailableProducts()
            enabled = True
        except Exception as e:
            logging.debug(e.message, exc_info=True)
            lang = get_solution_settings(service_user).main_language
            err = translate(lang, 'Invalid url (%(url)s). It must be reachable over http or https.', url=url)
            raise HttpBadRequestException(err)
    else:
        enabled = False
    if enabled != settings.enabled:
        set_updates_pending(service_user)
    settings.enabled = enabled
    settings.put()
    return settings


@cached(1, lifetime=DAY)
@returns(dict)
@arguments(url=unicode, username=unicode, password=unicode, product_id=unicode)
def get_product_details(url, username, password, product_id):
    return serialize_object(get_jcc_client(url, username, password).service.getGovProductDetails(productID=product_id))


@cached(1, lifetime=DAY)
@returns(dict)
@arguments(url=unicode, username=unicode, password=unicode, location_id=unicode)
def get_location(url, username, password, location_id):
    return serialize_object(get_jcc_client(url, username, password).service
                            .getGovLocationDetails(locationID=location_id))


def get_appointments_for_user(settings, app_user):
    # type: (JCCSettings, users.User) -> dict
    user_appointments = JCCUserAppointments.create_key(settings.service_user, app_user).get()
    client = get_jcc_client(settings.url, settings.username, settings.password)
    appointments = []
    all_product_ids = set()
    all_location_ids = set()
    if user_appointments:
        now = datetime.now()
        for appointment in sorted(user_appointments.appointments, key=lambda a: a.start_date):
            if appointment.start_date > now:
                # getGovAppointmentExtendedDetails is not supported by all jcc environments apparently
                appointment_details = client.service.getGovAppointmentDetails(appID=appointment.id)
                serialized = serialize_object(appointment_details)
                serialized['id'] = appointment.id
                appointments.append(serialized)
                all_product_ids.update(appointment_details.productID.split(','))
                all_location_ids.add(appointment_details.locationID)
    # TODO: In case this is too slow, store these in datastore models so we can get everything in 1 call
    product_details = {product_id: get_product_details(settings.url, settings.username, settings.password, product_id)
                       for product_id in all_product_ids}
    locations = {location_id: get_location(settings.url, settings.username, settings.password, location_id)
                 for location_id in all_location_ids}
    return {
        'appointments': appointments,
        'products': product_details,
        'locations': locations
    }


def add_appointment_to_calendar(settings, app_user, appointment_id):
    # type: (JCCSettings, users.User, str) -> dict
    user_appointments = JCCUserAppointments.create_key(settings.service_user,
                                                       app_user).get()  # type: JCCUserAppointments
    sln_settings = get_solution_settings(settings.service_user)
    for appointment in (user_appointments.appointments if user_appointments else []):
        if appointment.id == appointment_id:
            break
    else:
        return {'message': translate(sln_settings.main_language, 'appointment_not_found')}
    client = get_jcc_client(settings.url, settings.username, settings.password)
    appointment_details = client.service.getGovAppointmentDetails(appID=appointment_id)
    location = get_location(settings.url, settings.username, settings.password, appointment_details.locationID)
    all_product_ids_list = appointment_details.productID.split(',')
    all_product_ids = set(all_product_ids_list)
    products = {product_id: get_product_details(settings.url, settings.username, settings.password, product_id)
                for product_id in all_product_ids}
    create_ical_for_appointment(app_user, appointment_id, appointment_details, location, products,
                                all_product_ids_list[0], sln_settings.main_language)
    msg = translate(sln_settings.main_language, 'an_email_has_been_sent_with_appointment_event')
    return {'message': msg}


def create_ical_for_appointment(app_user, appointment_id, appointment, location, products, first_product_id, lang):
    # type: (users.User, str, CompoundValue, CompoundValue, Dict[str, CompoundValue], str, str) -> None
    cal = Calendar()
    cal.add('prodid', '-//Our City App//calendar//')
    cal.add('version', '2.0')
    cal.add('CALSCALE', 'GREGORIAN')
    cal.add('method', 'REQUEST')
    event = Event()
    event.add('uid', appointment_id)
    title = products[first_product_id]['description']
    event.add('summary', title)
    description_lines = [translate(lang, 'activities') + ':']
    for product in products.itervalues():
        description_lines.append('- %s' % product['description'])
    if appointment.appointmentDesc:
        description_lines.append(appointment.appointmentDesc)
    description = '\n'.join(description_lines)
    event.add('description', description)
    location_str = '%s, %s, %s %s' % (
        location['locationDesc'], location['address'], location['postalcode'], location['city'])
    event.add('location', location_str)
    event.add('dtstart', appointment.appStartTime)
    event.add('dtend', appointment.appEndTime)
    now = datetime.utcnow()
    event.add('dtstamp', now)
    event.add('created', now)
    event.add('updated', now)

    organizer_email = appointment.clientMail or get_human_user_from_app_user(app_user).email()
    organizer_name = '%s %s' % (appointment.clientInitials, appointment.clientLastName)
    organizer = vCalAddress('MAILTO:%s' % organizer_email)
    organizer.params['cn'] = vText(organizer_name)

    event.add('organizer', organizer)
    cal.add_component(event)

    to_email = organizer_email or get_human_user_from_app_user(app_user).email()
    app_id = get_app_id_from_app_user(app_user)
    app = get_app(app_id)
    from_ = '%s <%s>' % (app.name, app.dashboard_email_address)
    ical_attachment = ('%s.ics' % title, b64encode(cal.to_ical()))
    subject = title
    when = '%s, %s - %s' % (
        format_date(appointment.appStartTime, format='full', locale=lang),
        format_time(appointment.appStartTime, format='short', locale=lang),
        format_time(appointment.appEndTime, format='short', locale=lang),
    )
    body = [
        title,
        '',
        '%s: %s' % (translate(lang, 'when'), when),
    ]

    if location:
        body.append('%s: %s' % (translate(lang, 'oca.location'), location_str))
    if appointment.appointmentDesc:
        body.append(description)

    send_mail(from_, to_email, subject, '\n'.join(body), attachments=[ical_attachment])


def _after_appointment_booked(settings_key, app_user, appointment_id):
    # type: (ndb.Key, users.User, str) -> None
    settings = settings_key.get()  # type: JCCSettings
    client = get_jcc_client(settings.url, settings.username, settings.password)
    appointment = client.service.getGovAppointmentDetails(appID=appointment_id)
    key = JCCUserAppointments.create_key(settings.service_user, app_user)
    user_appointments = key.get() or JCCUserAppointments(key=key)
    user_appointments.appointments.append(JCCAppointment(id=appointment_id, start_date=appointment.appStartTime))
    user_appointments.put()


def _handle_book_appointment(settings, app_user, arguments, result):
    # type: (JCCSettings, users.User, dict, CompoundValue) -> CompoundValue
    if result.updateStatus == 0:
        deferred.defer(_after_appointment_booked, settings.key, app_user, result.appID)
    return result


def _after_required_fields(settings, app_user, arguments, required_fields):
    # type: (JCCSettings, users.User, dict, List[str]) -> CompoundValue
    field_set = {'clientDateOfBirth', 'clientLastName'}
    # Convert required fields to the real fields (AnyTel -> clientTel etc)
    for field in required_fields:
        if field == 'AnyTel':
            real_field = 'clientTel'
        elif field == 'Email':
            real_field = 'clientMail'
        else:
            # Not sure what the rest is since this isn't documented what the possible values are
            real_field = 'client%s' % field
        field_set.add(real_field)
    non_extended_fields = [
        'productID',
        'clientID',
        'clientLastName',
        'clientSex',
        'clientDateOfBirth',
        'clientInitials',
        'clientAddress',
        'clientPostalCode',
        'clientCity',
        'clientCountry',
        'clientTel',
        'clientMail',
        'locationID',
        'appStartTime',
        'appEndTime',
        'appointmentDesc',
        'caseID',
        'isClientVerified',
        'clientLanguage',
    ]
    is_extended = any(field not in non_extended_fields for field in field_set)
    if is_extended:
        field_set.add('clientFirstName')
    else:
        field_set.add('clientInitials')  # acts as firstname in this case
    return list(field_set)


def _delete_user_appointment(service_user, app_user, appointment_id):
    user_appointments = JCCUserAppointments.create_key(service_user, app_user).get()
    new_appointments = [a for a in user_appointments.appointments if a.id != appointment_id]
    user_appointments.appointments = new_appointments
    user_appointments.put()


def _after_appointment_deleted(settings, app_user, arguments, result):
    # type: (JCCSettings, users.User, dict, int) -> int
    if result == 0:
        deferred.defer(_delete_user_appointment, settings.service_user, app_user, arguments['appID'])
    return result


_post_call_handlers = {
    JccApiMethod.bookGovAppointment: _handle_book_appointment,
    JccApiMethod.bookGovAppointmentExtendedDetails: _handle_book_appointment,
    JccApiMethod.GetRequiredClientFields: _after_required_fields,
    JccApiMethod.deleteGovAppointment: _after_appointment_deleted,
}


def _do_call(client, call_name, arguments):
    # type: (Client, str, dict) -> CompoundValue
    method = getattr(client.service, call_name)
    return method(**arguments)


def custom_converter(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    else:
        return serialize_object(obj)


def handle_method(service_user, email, method, params, tag, service_identity, user_details):
    # type: (users.User, str, str, str, str, str, list[UserDetailsTO]) -> SendApiCallCallbackResultTO
    response = SendApiCallCallbackResultTO()
    try:
        settings = get_jcc_settings(service_user)
        client = get_jcc_client(settings.url, settings.username, settings.password)
        json_data = json.loads(params) if params else {}
        app_user = user_details[0].toAppUser()
        if method not in JccApiMethod.all():
            raise Exception('Jcc method not found: %s' % method)
        if method == JccApiMethod.GET_APPOINTMENTS:
            result = get_appointments_for_user(settings, app_user)
        elif method == JccApiMethod.ADD_TO_CALENDAR:
            result = add_appointment_to_calendar(settings, app_user, json_data['appointmentID'])
        else:
            if method == JccApiMethod.bookGovAppointmentExtendedDetails:
                if _should_add_recurring(client) and 'isRecurring' not in json_data['appDetail']:
                    json_data['appDetail']['isRecurring'] = False

            result = _do_call(client, method, json_data)
        if method in _post_call_handlers:
            result = _post_call_handlers[method](settings, app_user, json_data, result)
        if isinstance(result, unicode):
            response.result = result
        else:
            response.result = convert_to_unicode(json.dumps(result, default=custom_converter))
    except Exception:
        logging.error('Error while handling jcc call %s' % method, exc_info=True)
        sln_settings = get_solution_settings(service_user)
        response.error = translate(sln_settings.main_language, 'error-occured-unknown')
    return response


def _should_add_recurring(client):
    # type: (Client) -> bool
    types = client.wsdl.types  # type: Schema
    for type_ in types.types:  # type: zeep.xsd.Type
        if isinstance(type_, zeep.xsd.ComplexType) and type_.name == 'AppointmentFullDetaildWithFullCustomerDetailsType':
            return any(name == 'isRecurring' for name, element in type_.elements)
    return False
