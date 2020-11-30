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

import base64
import json
import logging
from cgi import FieldStorage
from datetime import datetime, timedelta
from types import NoneType

import dateutil.parser
import httplib2
import pytz
from babel.dates import format_datetime
from dateutil.relativedelta import relativedelta
from google.appengine.ext import deferred, ndb
from icalendar import Calendar, Event as ICalenderEvent, vText, vCalAddress
from oauth2client import client
from oauth2client.client import HttpAccessTokenRefreshError

from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.communities.models import AppFeatures
from rogerthat.consts import DEBUG
from rogerthat.dal import parent_ndb_key
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.profile import get_service_profile, get_user_profile
from rogerthat.models import App
from rogerthat.models.utils import ndb_allocate_ids
from rogerthat.rpc import users
from rogerthat.rpc.rpc import APPENGINE_APP_ID
from rogerthat.rpc.service import BusinessException
from rogerthat.settings import get_server_settings
from rogerthat.to.messaging import AttachmentTO
from rogerthat.to.service import SendApiCallCallbackResultTO, UserDetailsTO
from rogerthat.utils import send_mail, replace_url_with_forwarded_server
from rogerthat.utils.rfc3339 import rfc3339
from solution_server_settings import get_solution_server_settings
from solutions import translate, translate as common_translate
from solutions.common.bizz import SolutionModule, get_organization_type
from solutions.common.bizz.events.events_search import search_events, index_events, delete_events_from_index
from solutions.common.bizz.images import upload_file, remove_files
from solutions.common.dal import get_solution_settings, get_event_by_id
from solutions.common.models import SolutionSettings
from solutions.common.models.agenda import SolutionCalendar, SolutionGoogleCredentials, Event, EventPeriod, \
    EventCalendarType, EventDate, EventMedia, EventMediaType, EventAnnouncements
from solutions.common.to import EventItemTO, SolutionGoogleCalendarStatusTO, SolutionGoogleCalendarTO, \
    CreateEventItemTO, EventAnnouncementsTO, EventAnnouncementTO

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

API_METHOD_SOLUTION_EVENTS_LOAD = "solutions.events.load"
API_METHOD_SOLUTION_EVENTS_ANNOUNCEMENTS = "solutions.events.announcements"
API_METHOD_SOLUTION_EVENTS_ADDTOCALENDER = "solutions.events.addtocalender"


def _get_client_flow():
    if DEBUG:
        redirect_uri = "http://localhost:8080/common/events/google/oauth2callback"
    else:
        redirect_uri = "https://%s.appspot.com/common/events/google/oauth2callback" % APPENGINE_APP_ID
        redirect_uri = replace_url_with_forwarded_server(redirect_uri)

    solution_server_setting = get_solution_server_settings()
    flow = client.OAuth2WebServerFlow(client_id=solution_server_setting.solution_sync_calendar_events_client_id,
                                      client_secret=solution_server_setting.solution_sync_calendar_events_client_secret,
                                      scope='https://www.googleapis.com/auth/calendar.readonly email',
                                      redirect_uri=redirect_uri,
                                      approval_prompt='force')
    return flow


def get_google_authenticate_url(calendar_id):
    flow = _get_client_flow()
    url = flow.step1_get_authorize_url(state=calendar_id)
    return url


@returns(SolutionGoogleCalendarStatusTO)
@arguments(service_user=users.User, calendar_id=(int, long))
def get_google_calendars(service_user, calendar_id):
    from apiclient.discovery import build
    sln_settings = get_solution_settings(service_user)

    sc = SolutionCalendar.create_key(calendar_id, service_user, sln_settings.solution).get()
    google_credentials = google_calendar_ids = None
    if sc:
        google_credentials = sc.get_google_credentials()
        google_calendar_ids = sc.google_calendar_ids

    result = SolutionGoogleCalendarStatusTO()
    result.enabled = False
    result.calendars = []
    if google_credentials:
        logging.debug("access_token_expired: %s", google_credentials.access_token_expired)
        if google_credentials.access_token_expired:
            return result

        http_auth = google_credentials.authorize(httplib2.Http())
        calendar_service = build('calendar', 'v3', http=http_auth)
        try:
            result.enabled = True
            calendar_list = calendar_service.calendarList().list().execute(http=http_auth)
            if calendar_list['items']:
                for c in calendar_list['items']:
                    calendar_to = SolutionGoogleCalendarTO()
                    calendar_to.key = c["id"]
                    calendar_to.label = c["summary"]
                    calendar_to.enabled = calendar_to.key in google_calendar_ids
                    result.calendars.append(calendar_to)
        except:
            result.enabled = False
            result.calendars = []
            logging.warn(u"Error while loading calendars", exc_info=1)

    return result


def save_google_credentials(service_user, calendar_id, code):
    from apiclient.discovery import build
    flow = _get_client_flow()
    credentials = flow.step2_exchange(code=code)
    http_auth = credentials.authorize(httplib2.Http())
    userinfo_service = build('oauth2', 'v2', http=http_auth)
    try:
        user_info = userinfo_service.userinfo().get().execute()
        logging.info(user_info)
        if user_info and user_info.get('id'):
            deferred.defer(_save_google_credentials, service_user, calendar_id, user_info, credentials)
            return True
    except Exception as e:
        logging.error('An error occurred while saving google credentials: %s', e)
    return False


def _save_google_credentials(service_user, calendar_id, user_info, credentials):
    sln_settings = get_solution_settings(service_user)

    @ndb.transactional(xg=True)
    def trans():
        credentails_model = SolutionGoogleCredentials(key=SolutionGoogleCredentials.create_key(user_info['id']))
        credentails_model.email = user_info.get('email')
        credentails_model.name = user_info.get('name')
        credentails_model.gender = user_info.get('gender')
        credentails_model.picture = user_info.get('picture')
        credentails_model.credentials = credentials
        credentails_model.put()  # we still need to save this because other calendars can be using the same credential
        calendar = SolutionCalendar.create_key(calendar_id, service_user, sln_settings.solution).get()
        if not calendar:
            return
        calendar.google_credentials = user_info['id']
        calendar.put()

    trans()


def update_events_from_google(service_user, calendar_id):
    from googleapiclient.errors import HttpError
    from apiclient.discovery import build
    sln_settings = get_solution_settings(service_user)

    sc = SolutionCalendar.create_key(calendar_id, service_user, sln_settings.solution).get()
    google_credentials = sc.get_google_credentials()
    google_calendar_ids = sc.google_calendar_ids

    if google_credentials and google_calendar_ids:
        logging.debug("access_token_expired: %s", google_credentials.access_token_expired)
        http_auth = google_credentials.authorize(httplib2.Http())
        calendar_service = build('calendar', 'v3', http=http_auth)

        date_now = datetime.now()
        time_min = rfc3339(date_now, utc=True)
        date_next_year = date_now + relativedelta(years=1)
        time_max = rfc3339(date_next_year, utc=True)

        for google_calendar_id in google_calendar_ids:
            page_token = None
            while True:
                try:
                    events = calendar_service.events().list(calendarId=google_calendar_id, maxResults=200,
                                                            pageToken=page_token, singleEvents=True, timeMin=time_min,
                                                            timeMax=time_max, showDeleted=True).execute(http=http_auth)
                except (HttpError, HttpAccessTokenRefreshError) as e:
                    logging.warning(u'Could not update google calendars for calendar_id %s and service_user %s: %s',
                                    google_calendar_id, service_user, e.message)
                    sc.google_credentials = None
                    sc.put()

                    break
                page_token = events.get('nextPageToken')
                if events['items']:
                    deferred.defer(put_google_events, service_user, calendar_id,
                                   sln_settings.solution, events['items'], sln_settings.main_language)
                if not page_token:
                    break


def put_google_events(service_user, calendar_id, solution, google_events, language):
    to_put = []
    no_title_text = common_translate(language, '(No title)')
    community_id = get_service_profile(service_user).community_id
    for google_event in google_events:
        google_event_id = google_event['id']
        try:
            logging.debug(google_event)
            event_parent_key = parent_ndb_key(service_user, solution)
            event = Event.list_by_source_and_id(event_parent_key, Event.SOURCE_GOOGLE_CALENDAR, google_event_id).get()
            event_exists = event is not None
            if not event:
                event = Event(parent=event_parent_key,
                              source=Event.SOURCE_GOOGLE_CALENDAR,
                              external_id=google_event_id)

            if google_event.get("status", "confirmed") == "cancelled":
                if not event_exists:
                    continue
                event.deleted = True
            else:
                event.deleted = False
            event.community_id = community_id
            event.organization_type = get_organization_type(service_user)
            event.title = google_event.get('summary', no_title_text)
            event.place = google_event.get("location", u"").replace(u"\n", u" ")
            event.organizer = google_event.get("organizer", {}).get("displayName", u"")
            event.description = google_event.get('description', u"")
            event.calendar_id = calendar_id
            event.external_link = google_event["htmlLink"]

            start_date = end_date = None
            start = google_event['start']
            end = google_event['end']
            # TODO properly support recurring events when asked for
            if 'dateTime' in start:
                start_date = dateutil.parser.parse(start['dateTime']).replace(tzinfo=None)
                end_date = dateutil.parser.parse(end['dateTime']).replace(tzinfo=None)
                event.calendar_type = EventCalendarType.SINGLE
            elif 'date' in start:
                start_date = dateutil.parser.parse(start['date']).replace(tzinfo=None)
                # A 1 day event will always have its end date set to the day after the start day in google calendar.
                # We're changing that here so that it is set to the same day instead.
                end_date = dateutil.parser.parse(end['date']).replace(tzinfo=None) - timedelta(days=1)
                event.periods = [EventPeriod(start=EventDate(date=start_date), end=EventDate(date=end_date))]
                event.calendar_type = EventCalendarType.SINGLE
            if start_date:
                event.start_date = start_date
                event.end_date = end_date
                to_put.append(event)
            else:
                logging.info('Skipping event %s because it had no start date', google_event_id)
                logging.debug(google_event)
        except Exception:
            logging.warn('Failed to put Google Event: %s', google_event)
            raise

    if to_put:
        ndb.put_multi(to_put)
        index_events(to_put)


@ndb.transactional(xg=True)
@returns(Event)
@arguments(sln_settings=SolutionSettings, new_event=CreateEventItemTO, community_id=(int, long),
           organization_type=(int, long))
def put_event(sln_settings, new_event, community_id, organization_type):
    # type: (SolutionSettings, CreateEventItemTO, int, int) -> Event
    service_user = sln_settings.service_user

    if not new_event.periods:
        raise BusinessException(common_translate(sln_settings.main_language, 'event-date-required'))

    if not new_event.title:
        raise BusinessException(common_translate(sln_settings.main_language, 'Title is required'))

    if new_event.external_link is MISSING:
        new_event.external_link = None

    if new_event.external_link:
        from solutions.common.bizz.messaging import validate_broadcast_url

        new_event.external_link = new_event.external_link.strip()
        if new_event.external_link:
            if not (new_event.external_link.startswith("http://") or new_event.external_link.startswith("https://")):
                new_event.external_link = "https://%s" % new_event.external_link
            validate_broadcast_url(new_event.external_link, sln_settings.main_language)
        else:
            new_event.external_link = None

    if new_event.id is not MISSING:
        event = get_event_by_id(service_user, sln_settings.solution, new_event.id)
    else:
        event_id = ndb_allocate_ids(Event, 1, parent_ndb_key(service_user, sln_settings.solution))[0]
        event = Event(key=Event.create_key(event_id, service_user, sln_settings.solution))

    picture = MISSING.default(new_event.picture, None)
    new_media_urls = [m.url for m in new_event.media]
    files_to_remove = []
    for existing_media in event.media:
        if existing_media.url not in new_media_urls and existing_media.ref:
            files_to_remove.append(existing_media.ref)
    remove_files(files_to_remove)

    if picture:
        event.media = []
        upload_event_image(picture, event)
    else:
        event.media = [EventMedia(url=media.url, type=media.type, copyright=MISSING.default(media.copyright, None))
                       for media in new_event.media]
    periods = []
    for period in new_event.periods:
        start_date = dateutil.parser.parse(period.start.datetime).replace(tzinfo=None)
        end_date = dateutil.parser.parse(period.end.datetime).replace(tzinfo=None)
        if end_date < start_date:
            end_date = end_date + relativedelta(days=1)
        periods.append(EventPeriod(start=EventDate(datetime=start_date), end=EventDate(datetime=end_date)))
    periods = sorted(periods, key=lambda p: p.start.datetime)
    event.calendar_type = EventCalendarType.MULTIPLE if len(periods) > 1 else EventCalendarType.SINGLE
    event.community_id = community_id
    event.organization_type = organization_type
    event.title = new_event.title
    event.place = new_event.place
    event.organizer = new_event.organizer
    event.description = new_event.description
    event.periods = [] if event.calendar_type == EventCalendarType.SINGLE else periods
    event.start_date = periods[0].start.datetime
    event.end_date = periods[-1].end.datetime
    event.url = new_event.external_link
    event.calendar_id = new_event.calendar_id
    event.put()
    index_events([event])

    return event


def upload_event_image(picture, event):
    meta, img_b64 = picture.split(',')
    img_str = base64.b64decode(img_b64)
    content_type = AttachmentTO.CONTENT_TYPE_IMG_PNG if AttachmentTO.CONTENT_TYPE_IMG_PNG in meta else AttachmentTO.CONTENT_TYPE_IMG_JPG
    uploaded_file = FieldStorage(StringIO(img_str), headers={'content-type': content_type})
    uploaded_file_model = upload_file(event.service_user, uploaded_file, 'events', event.key)
    event.media = [EventMedia(url=uploaded_file_model.url, type=EventMediaType.IMAGE, ref=uploaded_file_model.key)]


@returns(NoneType)
@arguments(service_user=users.User, event_id=(int, long))
def delete_event(service_user, event_id):
    settings = get_solution_settings(service_user)
    event = get_event_by_id(service_user, settings.solution, event_id)
    if event:
        delete_events_from_index([event.key])
        if event.source == Event.SOURCE_CMS:
            remove_files([media.ref for media in event.media if media.ref])
            event.key.delete()
        else:
            event.deleted = True
            event.put()


@returns(SendApiCallCallbackResultTO)
@arguments(service_user=users.User, email=unicode, method=unicode, params=unicode, tag=unicode,
           service_identity=unicode,
           user_details=[UserDetailsTO])
def solution_load_events(service_user, email, method, params, tag, service_identity, user_details):
    r = SendApiCallCallbackResultTO()
    sln_settings = get_solution_settings(service_user)
    data = json.loads(params)
    data_correct = 'startDate' in data
    if data_correct:
        data_correct = data['startDate'] < data['endDate']
    if not data_correct:
        r.result = json.dumps({
            'events': [],
            'has_more': False,
            'cursor': None,
        }).decode('utf8')
        return r
    cursor = data.get('cursor', None)

    community_id = None
    service = None
    if SolutionModule.CITY_APP in sln_settings.modules:
        profile = get_service_profile(service_user)
        community = get_community(profile.community_id)
        if AppFeatures.EVENTS_SHOW_MERCHANTS in community.features:
            community_id = community.id
    if not community_id:
        service = service_user.email()
    cursor, events = search_events(data['startDate'], data['endDate'], community_id, service, data.get('query'), cursor,
                                   15)
    base_url = get_server_settings().baseUrl
    r.result = json.dumps({
        'events': [EventItemTO.from_model(e, base_url, service_user=service_user).to_dict() for e in events],
        'has_more': cursor is not None,
        'cursor': cursor,
    }).decode('utf8')
    return r


@returns(SendApiCallCallbackResultTO)
@arguments(service_user=users.User, email=unicode, method=unicode, params=unicode, tag=unicode,
           service_identity=unicode,
           user_details=[UserDetailsTO])
def get_events_announcements(service_user, email, method, params, tag, service_identity, user_details):
    r = SendApiCallCallbackResultTO()

    user_profile = get_user_profile(user_details[0].toAppUser())
    country = get_community(user_profile.community_id).country
    announcements = EventAnnouncements.create_key(country).get()  # type: EventAnnouncements
    if not announcements:
        r.result = json.dumps(EventAnnouncementsTO(items=[]).to_dict()).decode('utf-8')
        return r
    desired_lang = user_profile.language  # type: unicode
    result = EventAnnouncementsTO(items=[])
    for title in announcements.titles:
        if desired_lang.startswith(title.language):
            result.title = title.text
            result.title_theme = title.theme
            break
    for announcement in announcements.items:
        if desired_lang.startswith(announcement.language):
            item = EventAnnouncementTO()
            item.title = announcement.title
            item.description = announcement.description
            item.image_url = announcement.image_url
            result.items.append(item)
    r.result = json.dumps(result.to_dict()).decode('utf-8')
    return r


@returns(SendApiCallCallbackResultTO)
@arguments(service_user=users.User, email=unicode, method=unicode, params=unicode, tag=unicode,
           service_identity=unicode,
           user_details=[UserDetailsTO])
def add_event_to_calender(service_user, email, method, params, tag, service_identity, user_details):
    result = SendApiCallCallbackResultTO()
    rogerthat_settings = get_server_settings()
    app = get_app_by_id(user_details[0].app_id)

    jsondata = json.loads(params)
    event_id = jsondata['id']
    service_user = users.User(jsondata['service_user_email'])
    date = dateutil.parser.parse(jsondata['date']).replace(tzinfo=None)

    sln_settings = get_solution_settings(service_user)
    lang = sln_settings.main_language
    event = get_event_by_id(service_user, sln_settings.solution, event_id)
    if not event:
        result.error = translate(lang, 'this_event_has_ended')
        return result
    start_date, end_date = event.get_closest_occurrence(date)
    if not start_date:
        result.error = translate(lang, 'this_event_has_ended')
        return result
    email_subject = '%s: %s' % (translate(lang, 'event'), event.title)

    dtstart = (start_date.date or start_date.datetime).replace(tzinfo=sln_settings.tz_info)
    dtend = (end_date.date or end_date.datetime).replace(tzinfo=sln_settings.tz_info)

    when = '%s - %s' % (
        format_datetime(dtstart, format='medium', locale=lang),
        format_datetime(dtend, format='medium', locale=lang),
    )
    body = [
        event.title,
        '',
    ]
    if event.description:
        body.append(event.description)
    body.append('%s: %s' % (translate(lang, 'when'), when))
    if event.place:
        body.append('%s: %s' % (translate(lang, 'oca.location'), event.place))

    cal = Calendar()
    cal.add('prodid', '-//Our City App//calendar//')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST')
    calendar_event = ICalenderEvent()
    calendar_event.add('summary', event.title)
    calendar_event.add('description', event.description)
    calendar_event.add('location', event.place)

    now_date = datetime.now()
    dtstamp = now_date.replace(tzinfo=pytz.utc)
    calendar_event.add('dtstart', dtstart)
    calendar_event.add('dtend', dtend)
    calendar_event.add('dtstamp', dtstamp)

    calendar_event.add('uid', '%s %s' % (app.dashboard_email_address, event.id))

    organizer = vCalAddress('MAILTO:%s' % app.dashboard_email_address)
    organizer.params['cn'] = vText(event.organizer or sln_settings.name)
    calendar_event.add('organizer', organizer)

    cal.add_component(calendar_event)

    attachments = [('event.ics', base64.b64encode(cal.to_ical()))]

    from_ = rogerthat_settings.senderEmail if app.type == App.APP_TYPE_ROGERTHAT else (
        '%s <%s>' % (app.name, app.dashboard_email_address))
    send_mail(from_, email, email_subject, '\n'.join(body), attachments=attachments)

    msg = translate(lang, 'an_email_has_been_sent_with_event_details')
    result.result = json.dumps({'message': msg}).decode('utf-8')
    return result
