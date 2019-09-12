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

from collections import defaultdict
from datetime import datetime, timedelta
from hashlib import sha1
from hmac import new as hmac
import json
import logging
import pprint
from random import getrandbits
import time
from urllib import quote as urlquote
import urllib

import dateutil
from dateutil.relativedelta import relativedelta
from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred, ndb
import pytz
import webapp2

from rogerthat.bizz.job import run_job
from rogerthat.consts import DEBUG
from rogerthat.dal import parent_ndb_key
from rogerthat.utils import now, get_epoch_from_datetime
from shop.constants import MAPS_QUEUE
from solutions.common.bizz import get_default_app_id, get_organization_type
from solutions.common.bizz.cityapp import get_uitdatabank_events, \
    do_signed_uitdatabank_v2_request
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionSettings
from solutions.common.models.agenda import Event, NdbEvent, EventMedia, EventMediaType
from solutions.common.models.cityapp import UitdatabankSettings


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
        for sln_settings in SolutionSettings.all(projection=('uitdatabank_actor_id',)).filter('uitdatabank_actor_id >', ''):
            uitdatabank_actors[sln_settings.uitdatabank_actor_id].append(sln_settings.key())

        pagelength = 50
        uitdatabank_settings = uitdatabank_settings_key.get()
        logging.info("process_cityapp_uitdatabank_events for %s page %s", uitdatabank_settings.service_user, page)
        success, result = get_uitdatabank_events(uitdatabank_settings, page, pagelength, uitdatabank_settings.cron_sync_time or None)
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
        for r in result:
            result_count += 1
            if uitdatabank_settings.version in (UitdatabankSettings.VERSION_1, UitdatabankSettings.VERSION_2,):
                external_id = r['cdbid']
            else:
                external_id = r
            updated_events = _populate_uit_events(sln_settings, uitdatabank_settings, external_id, uitdatabank_actors)
            if updated_events:
                updated_events_count += 1
                to_put.extend(updated_events)

        logging.debug("Added/updated %s/%s events", updated_events_count, result_count)
        if to_put:
            ndb.put_multi(to_put)

        if result_count != 0:
            deferred.defer(_process_cityapp_uitdatabank_events, uitdatabank_settings_key, page + 1)
        else:
            uitdatabank_settings = uitdatabank_settings_key.get()
            uitdatabank_settings.cron_sync_time = uitdatabank_settings.cron_run_time
            uitdatabank_settings.put()
    except Exception as e:
        logging.exception(str(e), _suppress=False)


def get_dates_v1(r_timestamp):
    r_timestart = r_timestamp["timestart"]
    start_date = datetime.strptime("%s %s" % (r_timestamp["date"], r_timestart), "%Y-%m-%d %H:%M:%S")
    start_date = get_epoch_from_datetime(start_date)
    if r_timestamp.get("timeend", None):
        end_date = time.strptime(r_timestamp["timeend"], '%H:%M:%S')
        end_date = long(timedelta(hours=end_date.tm_hour, minutes=end_date.tm_min,
                                  seconds=end_date.tm_sec).total_seconds())
    else:
        end_date = 0
    return start_date, end_date


def get_dates_v2(r_timestamp):
    # type: (int) -> tuple[int, int]
    r_timestart = r_timestamp["timestart"]
    timestamp = long((r_timestamp["date"] + r_timestart) / 1000)
    tz = pytz.timezone('Europe/Brussels')
    dt_with_tz = datetime.fromtimestamp(timestamp, tz)
    dt_without_tz = datetime(dt_with_tz.year, dt_with_tz.month, dt_with_tz.day, dt_with_tz.hour,
                                      dt_with_tz.minute, dt_with_tz.second)
    time_epoch = get_epoch_from_datetime(dt_without_tz)
    time_diff = _get_time_diff_uitdatabank(dt_with_tz, dt_without_tz)
    start_date = time_epoch - time_diff
    if r_timestamp.get("timeend", None):
        end_date = int(r_timestamp["timeend"] / 1000) - time_diff
    else:
        end_date = 0
    return start_date, end_date


def get_event_start_and_end_dates(timestamps, v2=False):
    # type: (list[int], bool) -> tuple[list[int], list[int]]
    event_start_dates = []
    event_end_dates = []

    def get_dates(r_timestamp):
        if v2:
            start_date, end_date = get_dates_v2(r_timestamp)
        else:
            start_date, end_date = get_dates_v1(r_timestamp)

        event_start_dates.append(start_date)
        event_end_dates.append(end_date)

    r_timestamp = timestamps["timestamp"]
    if isinstance(r_timestamp, dict):
        logging.debug("dict timestamp: %s", r_timestamp)
        r_timestart = r_timestamp.get("timestart", None)
        if not r_timestart:
            logging.info("Skipping event because it had no starttime (dict)")
            return None, None
        get_dates(r_timestamp)
    elif isinstance(r_timestamp, list):
        logging.debug("list timestamp: %s", r_timestamp)
        for r_ts in r_timestamp:
            if r_ts.get("timestart"):
                get_dates(r_ts)

    return event_start_dates, event_end_dates


def _get_period_dates(period):
    # type: (dict) -> tuple[list[int], list[int]]
    """
    Examples:
      {
        "dateto": "2019-04-01",
        "weekscheme": {
          "monday": {
            "openingtime": {
              "to": "10:30:00",
              "from": "09:30:00"
            },
            "opentype": "open"
          },
          "tuesday": {
            "opentype": "closed"
          },
          "friday": {
            "opentype": "closed"
          },
          "wednesday": {
            "opentype": "closed"
          },
          "thursday": {
            "opentype": "closed"
          },
          "sunday": {
            "opentype": "closed"
          },
          "saturday": {
            "opentype": "closed"
          }
        },
        "datefrom": "2019-01-14"
      }
    """
    if not period:
        return [], []
    week_scheme = period.get('weekscheme')
    if not week_scheme:
        return [], []
    logging.debug('period:%s', period)
    date_format = '%Y-%m-%d'
    hour_format = '%H:%M:%S'
    if isinstance(period['datefrom'], (int, long)):
        start_date = datetime.utcfromtimestamp(period['datefrom'] / 1000)
        end_date = datetime.utcfromtimestamp(period['dateto'] / 1000)
    else:
        start_date = datetime.strptime(period['datefrom'], date_format)
        end_date = datetime.strptime(period['dateto'], date_format)
    days = (end_date - start_date).days + 1  # +1 to include the end date itself
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    start_dates = []
    end_dates = []

    for day in xrange(days):
        date = start_date + relativedelta(days=day)
        day_name = day_names[date.weekday()]
        scheme = week_scheme[day_name]
        is_open = scheme.get('opentype', 'closed') == 'open'
        if not is_open:
            continue
        opening_time = scheme.get('openingtime')
        if not opening_time:
            continue
        opening_times = [opening_time] if not isinstance(opening_time, list) else opening_time
        for open_time in opening_times:
            if isinstance(open_time['from'], (str, unicode)):
                from_ = datetime.strptime(open_time['from'], hour_format)
            else:
                from_ = datetime.utcfromtimestamp(open_time['from'] / 1000)

            if isinstance(open_time['to'], (str, unicode)):
                to = datetime.strptime(open_time['to'], hour_format)
            else:
                to = datetime.utcfromtimestamp(open_time['to'] / 1000)

            day_start_date = date + relativedelta(hours=from_.hour, minutes=from_.minute, seconds=from_.second)
            day_end_date = date + relativedelta(hours=to.hour, minutes=to.minute, seconds=to.second)
            start_date_timestamp = int(time.mktime(day_start_date.timetuple()))
            end_date_timestamp = int(time.mktime(day_end_date.timetuple()))
            start_dates.append(start_date_timestamp)
            end_dates.append(end_date_timestamp - start_date_timestamp)
    return start_dates, end_dates


def _populate_uit_events(sln_settings, uitdatabank_settings, external_id, uitdatabank_actors):
    logging.debug("process event with id: %s", external_id)
    detail_success, detail_result = _get_uitdatabank_events_detail(uitdatabank_settings, external_id)
    if not detail_success:
        logging.warn("Failed to get detail for cdbid: %s\n%s" % (external_id, detail_result))
        return None

    if uitdatabank_settings.version == UitdatabankSettings.VERSION_2 and uitdatabank_settings.cron_sync_time:
        if detail_result["lastupdated"] < (uitdatabank_settings.cron_sync_time * 1000):
            return None

    if DEBUG:
        logging.warn("detail result: %s", detail_result)

    if uitdatabank_settings.version in (UitdatabankSettings.VERSION_1, UitdatabankSettings.VERSION_2,):
        return _populate_uit_events_v1_or_v2(sln_settings, uitdatabank_settings.version, external_id, detail_result, uitdatabank_actors)
    else:
        return _populate_uit_events_v3(sln_settings, external_id, detail_result, uitdatabank_actors)


def filtered_join(sep, parts):
    return sep.join(filter(bool, parts))  # filtering None and empty strings


def get_event(sln_settings, external_id):
    event_parent_key = parent_ndb_key(sln_settings.service_user, sln_settings.solution)
    event = NdbEvent.list_by_source_and_id(event_parent_key, Event.SOURCE_UITDATABANK_BE, external_id).get()
    if not event:
        event = NdbEvent(parent=event_parent_key,
                         source=NdbEvent.SOURCE_UITDATABANK_BE,
                         external_id=external_id)

    event.app_ids = [get_default_app_id(sln_settings.service_user)]
    event.organization_type = get_organization_type(sln_settings.service_user)
    event.calendar_id = sln_settings.default_calendar
    return event


def fill_event_params(events, event_title, event_description, event_place, event_organizer, event_start_dates, event_end_dates):
    for event in events:
        event.title = event_title
        event.description = event_description
        event.place = event_place
        event.organize = event_organizer
        event.last_start_date = max(event_start_dates)
        event.start_dates = event_start_dates
        event.end_dates = event_end_dates
        event.first_start_date = event.get_first_event_date()


def get_organizer_settings(uitdatabank_actors, keys):
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
        organizer_event = NdbEvent.list_by_source_and_id(organizer_event_parent_key, Event.SOURCE_UITDATABANK_BE,
                                                         external_id).get()
        if not organizer_event:
            organizer_event = NdbEvent(parent=organizer_event_parent_key,
                                       source=NdbEvent.SOURCE_UITDATABANK_BE,
                                       external_id=external_id)

        organizer_event.app_ids = [get_default_app_id(service_user)]
        organizer_event.organization_type = get_organization_type(organizer_sln_settings.service_user)
        organizer_event.calendar_id = organizer_sln_settings.default_calendar
        events.append(organizer_event)
    return events


def _populate_uit_events_v1_or_v2(sln_settings, version, external_id, detail_result, uitdatabank_actors):

    def value(str_or_dict):
        if isinstance(str_or_dict, dict):
            return str_or_dict['value']
        return str_or_dict

    event = get_event(sln_settings, external_id)
    events = [event]

    # Matching organizers based on createdby, lastupdatedby, organiser.label.value and organiser.label.cbid
    uitdatabank_created_by = detail_result.get("createdby")
    uitdatabank_lastupdated_by = detail_result.get("lastupdatedby")

    uitdatabank_organizer_name = uitdatabank_organizer_cdbid = None
    if detail_result.get('organiser'):
        organizer = detail_result['organiser'].get('label')
        if isinstance(organizer, dict):
            uitdatabank_organizer_name = detail_result['organiser']['label'].get('value')
            uitdatabank_organizer_cdbid = detail_result['organiser']['label'].get('cdbid')
        else:
            uitdatabank_organizer_name = organizer

    logging.debug('Organizer info: %r', {
        'created_by': uitdatabank_created_by,
        'lastupdated_by': uitdatabank_lastupdated_by,
        'organizer_name': uitdatabank_organizer_name,
        'organizer_cbdid': uitdatabank_organizer_cdbid,
    })

    if uitdatabank_created_by or uitdatabank_lastupdated_by:
        organizer_settings = get_organizer_settings(uitdatabank_actors, [uitdatabank_created_by,
                                                                         uitdatabank_lastupdated_by,
                                                                         uitdatabank_organizer_name,
                                                                         uitdatabank_organizer_cdbid])
        events.extend(get_organizer_events(sln_settings.service_user, external_id, organizer_settings))

    r_event_detail = detail_result["eventdetails"]["eventdetail"]
    if not r_event_detail:
        logging.warn('Missing eventdetail')
        return None

    if isinstance(r_event_detail, list):
        for x in r_event_detail:
            if x['lang'] == sln_settings.main_language:
                r_event_detail = x
                break
        else:
            r_event_detail = r_event_detail[0]

    event_title = r_event_detail["title"]
    event_description = r_event_detail.get("shortdescription", r_event_detail.get("longdescription", u""))
    media = r_event_detail.get('media')
    if media:
        media_files = media['file']
        for media_file in media_files:
            if isinstance(media_file, dict) and media_file['mediatype'] == 'photo':
                event.media.append(EventMedia(
                    url=media_file['hlink'],
                    type=EventMediaType.IMAGE,
                    copyright=media_file.get('copyright'),
                ))

    location = detail_result["location"]["address"].get("physical")

    if location:
        street = location.get("street")
        if street:
            street = filtered_join(' ', (value(street), location.get('housenr')))
        city = filtered_join(' ', (location["zipcode"], value(location["city"])))
        event_place = filtered_join(', ', (street, city))
    else:
        event_place = detail_result["location"]["address"]["virtual"]["title"]

    r_organizer = detail_result.get('organiser')
    for k in ('actor', 'actordetails', 'actordetail', 'title'):
        if not r_organizer:
            break
        r_organizer = r_organizer.get(k)
    event_organizer = r_organizer

    r_timestamps = detail_result["calendar"].get("timestamps")
    if r_timestamps:
        event_start_dates, event_end_dates = get_event_start_and_end_dates(r_timestamps, v2=version == UitdatabankSettings.VERSION_2)
    else:
        periods = detail_result['calendar'].get('periods')
        event_start_dates, event_end_dates = _get_period_dates(periods and periods.get('period'))
    if not event_start_dates:
        logging.info("Skipping event because it had no starttime (list) for:\n%s", pprint.pformat(detail_result))
        return None

    fill_event_params(events, event_title, event_description, event_place, event_organizer, event_start_dates, event_end_dates)
    return events


def _populate_uit_events_v3(sln_settings, external_url, detail_result, uitdatabank_actors):
    lang = 'nl'
    if lang not in detail_result['languages']:
        return []
    if lang not in detail_result['completedLanguages']:
        return []

    external_id = external_url.rsplit('/')[1]
    event = get_event(sln_settings, external_id)
    events = [event]

    uitdatabank_created_by = detail_result.get("creator")
    uitdatabank_organizer_name = uitdatabank_organizer_cdbid = None
    if detail_result.get('organizer'):
        organizer_name = detail_result['organizer'].get('name') or {}
        if isinstance(organizer_name, dict):
            uitdatabank_organizer_name = organizer_name.get(lang)
        else:
            uitdatabank_organizer_name = organizer_name
        if '@id' in detail_result['organizer']:
            uitdatabank_organizer_cdbid = detail_result['organizer']['@id'].rsplit('/')[0]

    logging.debug('Organizer info: %r', {
        'created_by': uitdatabank_created_by,
        'organizer_name': uitdatabank_organizer_name,
        'organizer_cbdid': uitdatabank_organizer_cdbid,
    })

    if uitdatabank_created_by:
        organizer_settings = get_organizer_settings(uitdatabank_actors, [uitdatabank_created_by,
                                                                         uitdatabank_organizer_name,
                                                                         uitdatabank_organizer_cdbid])
        events.extend(get_organizer_events(sln_settings.service_user, external_id, organizer_settings))

    event_title = detail_result['name'][lang]
    event_description = None
    if detail_result.get('description'):
        event_description = detail_result['description'][lang]
    event_place = None
    event_organizer = uitdatabank_organizer_name
    media_objects = detail_result.get('mediaObject') or []
    for m in media_objects:
        if m['@type'] != 'schema:ImageObject':
            continue
        event.media.append(EventMedia(
            url=m['contentUrl'],
            type=EventMediaType.IMAGE,
            copyright=m.get('copyrightHolder'),
        ))

    location = detail_result.get('location')
    if location:
        address = detail_result['location'].get('address')
        if address:
            if lang in address:
                address = address[lang]
            street = address.get('streetAddress')
            city_name = address.get('addressLocality')
            postalCode = address.get('postalCode')
            city = filtered_join(', ', (postalCode, city_name))
            event_place = filtered_join(', ', (street, city))
        else:
            event_place = detail_result['location']['name']['nl']

    event_start_dates = []
    event_end_dates = []

    if detail_result['calendarType'] in ('single', 'multiple',):
        for sub_event in detail_result['subEvent']:
            start_date = dateutil.parser.parse(sub_event['startDate'])
            end_date = dateutil.parser.parse(sub_event['endDate'])
            start_date_timestamp = get_epoch_from_datetime(start_date.replace(tzinfo=None)) - long(start_date.utcoffset().total_seconds())
            end_date_timestamp = get_epoch_from_datetime(end_date.replace(tzinfo=None)) - long(end_date.utcoffset().total_seconds())

            start_timezone_offset = long(datetime.fromtimestamp(start_date_timestamp, tz=pytz.timezone(sln_settings.timezone)).utcoffset().total_seconds())
            end_timezone_offset = long(datetime.fromtimestamp(end_date_timestamp, tz=pytz.timezone(sln_settings.timezone)).utcoffset().total_seconds())

            start_date_timestamp_tz = start_date_timestamp + start_timezone_offset
            end_date_timestamp_tz = end_date_timestamp + end_timezone_offset

            event_start_dates.append(start_date_timestamp_tz)
            event_end_dates.append(end_date_timestamp_tz - start_date_timestamp_tz)

    elif detail_result['calendarType'] == 'periodic' and detail_result.get('openingHours'):
        start_date_tz = dateutil.parser.parse(detail_result['startDate'])
        end_date_tz = dateutil.parser.parse(detail_result['endDate'])
        start_date_epoch = get_epoch_from_datetime(start_date_tz.replace(tzinfo=None)) - long(start_date_tz.utcoffset().total_seconds())
        end_date_epoch = get_epoch_from_datetime(end_date_tz.replace(tzinfo=None)) - long(end_date_tz.utcoffset().total_seconds())
        start_date = datetime.utcfromtimestamp(start_date_epoch).date()
        end_date = datetime.utcfromtimestamp(end_date_epoch).date()

        days = (end_date - start_date).days + 1  # +1 to include the end date itself
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        hour_format = '%H:%M'
        for day in xrange(days):
            date = start_date + relativedelta(days=day)
            day_name = day_names[date.weekday()]

            for oh in detail_result['openingHours']:
                if day_name not in oh['dayOfWeek']:
                    continue

                from_ = datetime.strptime(oh['opens'], hour_format)
                to = datetime.strptime(oh['closes'], hour_format)

                day_start_date = date + relativedelta(hours=from_.hour, minutes=from_.minute, seconds=from_.second)
                day_end_date = date + relativedelta(hours=to.hour, minutes=to.minute, seconds=to.second)
                start_date_timestamp = get_epoch_from_datetime(day_start_date)
                end_date_timestamp = get_epoch_from_datetime(day_end_date)
                event_start_dates.append(start_date_timestamp)
                event_end_dates.append(end_date_timestamp - start_date_timestamp)

    if not event_start_dates:
        logging.info("Skipping event because it had no dates for:\n%s", pprint.pformat(detail_result))
        return None

    fill_event_params(events, event_title, event_description, event_place, event_organizer, event_start_dates, event_end_dates)
    return events


def _get_time_diff_uitdatabank(dt_with_tz, dt_without_tz):
    time_diff = int((dt_with_tz - pytz.UTC.localize(dt_without_tz)).total_seconds())
    if time_diff == -7200:
        return -3600  # Thre json response from uitdatabank is incorrect
    return time_diff


def _get_uitdatabank_events_detail(settings, external_id):
    if settings.version == UitdatabankSettings.VERSION_1:
        return _get_uitdatabank_events_detail_v1(settings, external_id)
    elif settings.version == UitdatabankSettings.VERSION_2:
        return _get_uitdatabank_events_detail_v2(settings, external_id)
    elif settings.version == UitdatabankSettings.VERSION_3:
        return _get_uitdatabank_events_detail_v3(settings, external_id)

    return False, 'Incorrect API version'


def _get_uitdatabank_events_detail_v1(settings, external_id):
    url = "http://build.uitdatabank.be/api/event/%s?" % external_id
    values = {'key': settings.params['key'],
              'format': "json"}
    data = urllib.urlencode(values)
    result = urlfetch.fetch(url + data, deadline=60)
    r = json.loads(result.content)

    if not isinstance(r, list):
        event = r.get("event")
        if event is not None:
            return True, event
    elif "error" in r[0]:
        return False, r[0]["error"]
    return False, "Unknown error occurred"


def _get_uitdatabank_events_detail_v2(settings, external_id):
    key = settings.params['key'].encode("utf8")
    secret = settings.params['secret'].encode("utf8")
    url = "https://www.uitid.be/uitid/rest/searchv2/detail/event/%s" % external_id

    result = do_signed_uitdatabank_v2_request(url, key, secret, deadline=60)
    if result.status_code != 200:
        return False, "Unknown error occurred status code"

    r = json.loads(result.content)['rootObject']
    if "error" in r[0]:
        return False, r[0]["error"]
    event = r[0].get("event")
    if event is not None:
        return True, event

    return False, "Unknown error occurred end"


def _get_uitdatabank_events_detail_v3(settings, external_id):
    result = urlfetch.fetch(external_id, deadline=60)
    if result.status_code != 200:
        return False, "Unknown error occurred status code"

    return True, json.loads(result.content)
