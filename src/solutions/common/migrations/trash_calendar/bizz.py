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

from datetime import datetime
import json
import logging

from google.appengine.api import urlfetch
from google.appengine.ext import ndb, deferred

from mcfw.rpc import returns, arguments
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import Message, UserProfileInfo, UserProfileInfoAddress
from rogerthat.rpc import users
from rogerthat.service.api import messaging
from rogerthat.to.messaging import MemberTO, AnswerTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils.app import get_app_user_tuple, create_app_user_by_email
from rogerthat.utils.cloud_tasks import schedule_tasks, create_task
from rogerthat.utils.location import geo_code
from solutions.common.migrations.trash_calendar.models import TrashCalendarTransferUser, \
    TrashCalendarTransferSettings

POKE_TAG_TRASH_CALENDAR_TRANSFER_ADDRESS = u'trash_calendar.transfer_address'
ANSWER_ID_TRANFER = u'tranfer'
ANSWER_ID_OTHER = u'other'
ANSWER_ID_NONE = u'none'


@returns()
@arguments(service_user=users.User, status=int, answer_id=unicode, received_timestamp=int, member=unicode,
           message_key=unicode, tag=unicode, acked_timestamp=int, parent_message_key=unicode, result_key=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def trash_transfer_address_pressed(service_user, status, answer_id, received_timestamp, member, message_key, tag,
                                   acked_timestamp, parent_message_key, result_key, service_identity, user_details):
    app_user = user_details[0].toAppUser()
    logging.info('trash_transfer_address_pressed app_user:%s answer_id:%s', app_user, answer_id)
    if not answer_id:
        return
    if answer_id == ANSWER_ID_TRANFER:
        deferred.defer(_tranfer_address, service_user, app_user, _queue=MIGRATION_QUEUE)

    deferred.defer(_delete_message_from_user, app_user, answer_id, _countdown=5, _queue=MIGRATION_QUEUE)

    
def send_messages_for_service(service_user, cursor=None):
    tcs = TrashCalendarTransferSettings.create_key(service_user).get()
    if not tcs:
        return

    params = {
        'app_id': tcs.app_id,
        'fetch_size': 100,
        'cursor': cursor
    }
    r = _do_trash_request(tcs, '/plugins/trash_calendar/admin/list_users', params)

    tasks = []
    for i in r['items']:
        app_user = create_app_user_by_email(i['email'], i['app_id'])
        tasks.append(create_task(_send_message_to_user, service_user, app_user, tcs.branding))

    if r.get('cursor'):
        tasks.append(create_task(send_messages_for_service, service_user, r['cursor']))

    if tasks:
        schedule_tasks(tasks, MIGRATION_QUEUE)


def _send_message_to_user(service_user, app_user, branding):
    tcu_key = TrashCalendarTransferUser.create_key(app_user)
    tcu = tcu_key.get()
    if tcu:
        logging.debug('_send_message_to_user TrashCalendarTransferUser already exists')
        return
    upi = UserProfileInfo.create_key(app_user).get()
    if upi and upi.addresses:
        logging.debug('_send_message_to_user user already has addresses')
        return
    up = get_user_profile(app_user)
    if not up:
        logging.debug('_send_message_to_user user_profile not found')
        return

    human_user, app_id = get_app_user_tuple(app_user)

    member = MemberTO()
    member.alert_flags = Message.ALERT_FLAG_VIBRATE
    member.member = human_user.email()
    member.app_id = app_id

    message = u'''Beste inwoner,

Vanaf vandaag is het mogelijk om nieuws te ontvangen op basis van locatie! Hierdoor zal u berichten krijgen van hinder, evenementen, festiviteiten en vele meer!

Om dit te kunnen ontvangen, dient u enkel uw adres in te geven.
We zien dat u dit reeds heeft ingesteld voor de afvalkalender. Wilt u hetzelfde adres gebruiken ? Klik dan op de knop 'Ja, gebruik hetzelfde adres'.

Om een ander adres te gebruiken, drukt u op de knop ' Ik wil een ander adres instellen'.'''

    answers = []
    btn = AnswerTO()
    btn.action = None
    btn.caption = u'Ja, gebruik hetzelfde adres'
    btn.id = ANSWER_ID_TRANFER
    btn.type = u'button'
    btn.ui_flags = 0
    answers.append(btn)

    btn = AnswerTO()
    btn.action = u'open://%s' % json.dumps({u'action': u'news'})
    btn.caption = u'Ik wil een ander adres instellen'
    btn.id = ANSWER_ID_OTHER
    btn.type = u'button'
    btn.ui_flags = 0
    answers.append(btn)

    btn = AnswerTO()
    btn.action = None
    btn.caption = u'Neen bedankt'
    btn.id = ANSWER_ID_NONE
    btn.type = u'button'
    btn.ui_flags = 0
    answers.append(btn)

    with users.set_user(service_user):
        parent_message_key = messaging.send(parent_key=None,
                                            parent_message_key=None,
                                            message=message,
                                            answers=answers,
                                            flags=Message.FLAG_AUTO_LOCK,
                                            members=[member],
                                            branding=branding,
                                            tag=POKE_TAG_TRASH_CALENDAR_TRANSFER_ADDRESS,
                                            service_identity=None)

    tcu = TrashCalendarTransferUser(key=tcu_key)
    tcu.service_user = service_user
    tcu.parent_message_key = parent_message_key
    tcu.answer_id = None
    tcu.put()


def _delete_message_from_user(app_user, answer_id):
    tcu = TrashCalendarTransferUser.create_key(app_user).get()
    if not tcu:
        return
    if tcu.answer_id:
        return
    tcu.answer_id = answer_id
    tcu.put()

    human_user, app_id = get_app_user_tuple(app_user)

    member = MemberTO()
    member.alert_flags = Message.ALERT_FLAG_SILENT
    member.member = human_user.email()
    member.app_id = app_id

    with users.set_user(tcu.service_user):
        messaging.delete_conversation(parent_message_key=tcu.parent_message_key,
                                      members=[member],
                                      service_identity=None)


def _tranfer_address(service_user, app_user):
    tcs = TrashCalendarTransferSettings.create_key(service_user).get()
    if not tcs:
        return

    human_user, app_id = get_app_user_tuple(app_user)
    params = {
        'app_id': tcs.app_id,
        'user': {
            'email': human_user.email(),
            'app_id': app_id
        }
    }

    r = _do_trash_request(tcs, '/plugins/trash_calendar/admin/get_user_data', params)

    country_code = u'BE'
    city = r['address']['city']
    zip_code = r['address']['zip_code']
    street_name = r['address']['street']
    house_nr = unicode(r['address']['house']['number'])
    bus_nr = unicode(r['address']['house']['bus'])

    address_string = street_name
    if house_nr:
        address_string += u' %s' % house_nr
    address_string += u', %s' % (zip_code)

    geocoded = geo_code(address_string, {'components': 'country:%s' % country_code})

    label = u'Thuis'
    distance = 3000

    upi_key = UserProfileInfo.create_key(app_user)
    upi = upi_key.get()
    if not upi:
        upi = UserProfileInfo(key=upi_key)
        upi.addresses = []

    address_uid = UserProfileInfoAddress.create_uid([country_code,
                                                     zip_code,
                                                     street_name,
                                                     house_nr,
                                                     bus_nr])

    street_uid = UserProfileInfoAddress.create_uid([country_code,
                                                    zip_code,
                                                    street_name])

    upia = UserProfileInfoAddress(created=datetime.now(),
                                  address_uid=address_uid,
                                  street_uid=street_uid,
                                  label=label,
                                  geo_location=ndb.GeoPt(geocoded['geometry']['location']['lat'],
                                                         geocoded['geometry']['location']['lng']),
                                  distance=distance,
                                  street_name=street_name,
                                  house_nr=house_nr,
                                  bus_nr=bus_nr,
                                  zip_code=zip_code,
                                  city=city,
                                  country_code=country_code)

    upi.addresses.append(upia)
    upi.put()


def _do_trash_request(tcs, base_url, params):
    url = '%s%s' % (tcs.base_url, base_url)

    headers = {
        'X-Nuntiuz-Service-Key': tcs.sik
    }

    logging.debug('_do_trash_request: %s params %s', url, params)

    result = urlfetch.fetch(url, json.dumps(params), method=urlfetch.POST, headers=headers, deadline=30, follow_redirects=False)

    if result.status_code != 200:
        logging.debug(result.status_code)
        logging.debug(result.content)
        raise Exception('Failed to execute trash request')

    return json.loads(result.content)
