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

import json
import logging
from collections import defaultdict
from datetime import datetime

import dateutil
import webapp2
from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred, ndb
from typing import Dict, List

from rogerthat.bizz.job import run_job
from rogerthat.consts import DEBUG
from rogerthat.dal import parent_ndb_key
from rogerthat.utils import now
from shop.constants import MAPS_QUEUE
from solutions.common.bizz import get_default_app_id, get_organization_type
from solutions.common.bizz.cityapp import get_uitdatabank_events
from solutions.common.bizz.events.events_search import index_events
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionSettings
from solutions.common.models.agenda import Event, EventMedia, EventMediaType, EventCalendarType, EventPeriod, \
    EventOpeningPeriod, EventDate
from solutions.common.models.cityapp import UitdatabankSettings
from solutions.common.utils import html_to_markdown


class CityAppSolutionEventsUitdatabank(webapp2.RequestHandler):

    def get(self):
        run_job(_get_uitdatabank_enabled_query, [],
                _process_cityapp_uitdatabank_events, [1], worker_queue=MAPS_QUEUE)


def _get_uitdatabank_enabled_query():
    return UitdatabankSettings.list_enabled()


def _process_cityapp_uitdatabank_events(uitdatabank_settings_key, page):
    try:
        uitdatabank_actors = defaultdict(list)  # type: dict[str, list[db.Key]]
        # Projection query - avoids need to fetch models
        for sln_settings in SolutionSettings.all(projection=('uitdatabank_actor_id',)).filter('uitdatabank_actor_id >',
                                                                                              ''):
            uitdatabank_actors[sln_settings.uitdatabank_actor_id].append(sln_settings.key())

        pagelength = 50
        uitdatabank_settings = uitdatabank_settings_key.get()
        logging.info("process_cityapp_uitdatabank_events for %s page %s", uitdatabank_settings.service_user, page)
        success, _, result = get_uitdatabank_events(uitdatabank_settings, page, pagelength,
                                                 uitdatabank_settings.cron_sync_time or None)
        if not success:
            if page == 1:
                logging.exception(result, _suppress=False)
            return

        if page == 1:
            uitdatabank_settings.cron_run_time = now()
            uitdatabank_settings.put()

        sln_settings = get_solution_settings(uitdatabank_settings.service_user)
        to_put = []

        result_count = 0
        updated_events_count = 0
        for external_id in result:
            result_count += 1
            updated_events = _populate_uit_events(sln_settings, uitdatabank_settings, external_id, uitdatabank_actors)
            if updated_events:
                updated_events_count += 1
                to_put.extend(updated_events)

        logging.debug("Added/updated %s/%s events", updated_events_count, result_count)
        if to_put:
            ndb.put_multi(to_put)
        index_events(to_put)

        if result_count != 0:
            deferred.defer(_process_cityapp_uitdatabank_events, uitdatabank_settings_key, page + 1)
        else:
            uitdatabank_settings = uitdatabank_settings_key.get()
            uitdatabank_settings.cron_sync_time = uitdatabank_settings.cron_run_time
            uitdatabank_settings.put()
    except Exception as e:
        logging.exception(str(e), _suppress=False)


def _populate_uit_events(sln_settings, uitdatabank_settings, external_id, uitdatabank_actors):
    logging.debug("process event with id: %s", external_id)
    detail_success, detail_result = _get_uitdatabank_events_detail(uitdatabank_settings, external_id)
    if not detail_success:
        logging.warn("Failed to get detail for id: %s\n%s" % (external_id, detail_result))
        return None

    if DEBUG:
        logging.debug("detail result: %s", detail_result)

    return _populate_uit_events_v3(sln_settings, external_id, detail_result, uitdatabank_actors)


def filtered_join(sep, parts):
    return sep.join(filter(bool, parts))  # filtering None and empty strings


def get_event(sln_settings, external_id):
    event_parent_key = parent_ndb_key(sln_settings.service_user, sln_settings.solution)
    event = Event.list_by_source_and_id(event_parent_key, Event.SOURCE_UITDATABANK_BE, external_id).get()
    if not event:
        event = Event(parent=event_parent_key,
                      source=Event.SOURCE_UITDATABANK_BE,
                      external_id=external_id)

    event.app_ids = [get_default_app_id(sln_settings.service_user)]
    event.organization_type = get_organization_type(sln_settings.service_user)
    event.calendar_id = sln_settings.default_calendar
    return event


def get_organizer_settings(uitdatabank_actors, keys):
    # type: (Dict[str, db.Key], List[str]) -> List[SolutionSettings]
    organizer_settings_keys = set()
    for k in keys:
        if not k:
            continue
        organizer_settings_keys.update(uitdatabank_actors.get(k, []))
    return db.get(organizer_settings_keys) if organizer_settings_keys else []


def get_organizer_events(service_user, external_id, organizer_settings):
    events = []
    logging.debug("organizer_settings: %s", map(repr, organizer_settings))
    for organizer_sln_settings in organizer_settings:
        organizer_event_parent_key = parent_ndb_key(organizer_sln_settings.service_user,
                                                    organizer_sln_settings.solution)
        organizer_event = Event.list_by_source_and_id(organizer_event_parent_key, Event.SOURCE_UITDATABANK_BE,
                                                      external_id).get()
        if not organizer_event:
            organizer_event = Event(parent=organizer_event_parent_key,
                                    source=Event.SOURCE_UITDATABANK_BE,
                                    external_id=external_id)

        organizer_event.app_ids = [get_default_app_id(service_user)]
        organizer_event.organization_type = get_organization_type(organizer_sln_settings.service_user)
        organizer_event.calendar_id = organizer_sln_settings.default_calendar
        events.append(organizer_event)
    return events


def _populate_uit_events_v3(sln_settings, external_url, detail_result, uitdatabank_actors):
    # type: (SolutionSettings, str, dict, Dict[str, db.Key]) -> List[Event]
    # https://documentatie.uitdatabank.be/content/json-ld-crud-api/latest/events.html
    lang = 'nl'
    if lang not in detail_result['languages']:
        return []
    if lang not in detail_result['completedLanguages']:
        return []

    external_id = external_url.rsplit('/', 1)[1]
    event = get_event(sln_settings, external_id)

    uitdatabank_created_by = detail_result.get("creator")
    uitdatabank_organizer_name = uitdatabank_organizer_cdbid = None
    if detail_result.get('organizer'):
        organizer_name = detail_result['organizer'].get('name') or {}
        if isinstance(organizer_name, dict):
            uitdatabank_organizer_name = organizer_name.get(lang)
        else:
            uitdatabank_organizer_name = organizer_name
        if '@id' in detail_result['organizer']:
            uitdatabank_organizer_cdbid = detail_result['organizer']['@id'].rsplit('/', 1)[1]

    logging.debug('Organizer info: %r', {
        'created_by': uitdatabank_created_by,
        'organizer_name': uitdatabank_organizer_name,
        'organizer_cbdid': uitdatabank_organizer_cdbid,
    })

    events = []
    # Filter events by creator id. Can be empty for main services
    if sln_settings.uitdatabank_actor_id:
        if sln_settings.uitdatabank_actor_id == uitdatabank_created_by:
            events.append(event)
    else:
        events.append(event)

    if uitdatabank_created_by and uitdatabank_created_by != sln_settings.uitdatabank_actor_id:
        organizer_settings = get_organizer_settings(uitdatabank_actors, [uitdatabank_created_by,
                                                                         uitdatabank_organizer_name,
                                                                         uitdatabank_organizer_cdbid])
        events.extend(get_organizer_events(sln_settings.service_user, external_id, organizer_settings))

    event_title = detail_result['name'][lang]
    event_description = None
    if detail_result.get('description'):
        event_description = html_to_markdown(detail_result['description'][lang])
    event_place = None
    event_organizer = uitdatabank_organizer_name
    media_objects = detail_result.get('mediaObject') or []
    media = []
    for m in media_objects:
        if m['@type'] != 'schema:ImageObject':
            continue
        media.append(EventMedia(
            url=m['contentUrl'],
            type=EventMediaType.IMAGE,
            copyright=m.get('copyrightHolder'),
        ))

    location = detail_result.get('location')
    if location and lang in detail_result['location']['name']:
        address = detail_result['location'].get('address')
        place_name = detail_result['location']['name'][lang]
        if address:
            if lang in address:
                address = address[lang]
            street = address.get('streetAddress')
            city_name = address.get('addressLocality')
            postal_code = address.get('postalCode')
            city = filtered_join(', ', (postal_code, city_name))
            event_place = filtered_join(', ', (place_name, street, city))
        else:
            event_place = detail_result['location']['name'][lang]
    start_date = None
    end_date = None
    dates = []
    opening_hours = []
    calendar_type = detail_result['calendarType']
    if calendar_type in (EventCalendarType.SINGLE, EventCalendarType.MULTIPLE,
                         EventCalendarType.PERIODIC):
        start_date = _parse_date(detail_result['startDate'])
        end_date = _parse_date(detail_result['endDate'])
    if calendar_type in (EventCalendarType.SINGLE, EventCalendarType.MULTIPLE):
        dates = [EventPeriod(start=EventDate(datetime=_parse_date(sub_event['startDate'])),
                             end=EventDate(datetime=_parse_date(sub_event['endDate'])))
                 for sub_event in detail_result['subEvent']]
    elif calendar_type in (EventCalendarType.PERIODIC, EventCalendarType.PERMANENT):
        # See https://documentatie.uitdatabank.be/content/json-ld-crud-api/latest/events/event-calendar.html
        day_mapping = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        for opening_hour in detail_result.get('openingHours', []):
            for day in opening_hour['dayOfWeek']:
                opening_hours.append(EventOpeningPeriod(open=opening_hour['opens'].replace(':', ''),
                                                        close=opening_hour['closes'].replace(':', ''),
                                                        day=day_mapping.index(day)))
    else:
        logging.debug(detail_result)
        raise Exception('Unknown calendar type %s' % calendar_type)

    external_link = u"https://www.uitinvlaanderen.be/agenda/e//%s" % external_id

    for event in events:
        event.title = event_title
        event.description = event_description
        event.place = event_place
        event.organizer = event_organizer
        event.media = media
        event.calendar_type = calendar_type
        event.start_date = start_date
        event.end_date = end_date
        event.periods = dates
        event.opening_hours = opening_hours
        event.external_link = external_link
    return events


def _parse_date(date_str):
    """Returns timezone unaware datetime from a timezone aware date string
    Args:
        date_str (str)

    Returns:
        datetime
    """
    parsed = dateutil.parser.parse(date_str)  # type: datetime
    return parsed.replace(tzinfo=None)


def _get_uitdatabank_events_detail(settings, external_id):
    if settings.version == UitdatabankSettings.VERSION_3:
        return _get_uitdatabank_events_detail_v3(settings, external_id)

    return False, 'Incorrect API version'


def _get_uitdatabank_events_detail_v3(settings, external_id):
    result = urlfetch.fetch(external_id, deadline=60)
    if result.status_code != 200:
        return False, result.content

    return True, json.loads(result.content)
