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

from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from google.appengine.ext import ndb
from oauth2client.contrib.appengine import CredentialsNDBProperty
from typing import Tuple, List

from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel
from rogerthat.rpc import users
from solutions.common.models.forms import UploadedFile


class EventMediaType(Enum):
    IMAGE = 'image'


class EventMedia(NdbModel):
    url = ndb.TextProperty()
    type = ndb.TextProperty(choices=EventMediaType.all())
    copyright = ndb.TextProperty()
    ref = ndb.KeyProperty(UploadedFile)


class EventDate(NdbModel):
    # Only one of both properties should be set - use 'date' for all-day events, datetime otherwise.
    date = ndb.DateProperty()
    datetime = ndb.DateTimeProperty()


class EventPeriod(NdbModel):
    start = ndb.StructuredProperty(EventDate)  # type: EventDate
    end = ndb.StructuredProperty(EventDate)  # type: EventDate


class EventOpeningPeriod(NdbModel):
    # Mapping from datetime.weekday to our mapping
    DAY_MAPPING = {
        0: 1,
        1: 2,
        2: 3,
        3: 4,
        4: 5,
        5: 6,
        6: 0,
    }
    open = ndb.StringProperty()  # 0000-2359
    close = ndb.StringProperty()
    # A number from 0–6, corresponding to the days of the week, starting on Sunday. For example, 2 means Tuesday.
    day = ndb.IntegerProperty()

    @property
    def opening_hour(self):
        return int(self.open[:2])

    @property
    def opening_minute(self):
        return int(self.open[2:])

    @property
    def close_hour(self):
        return int(self.close[:2])

    @property
    def close_minute(self):
        return int(self.close[2:])


class EventCalendarType(Enum):
    SINGLE = 'single'
    MULTIPLE = 'multiple'
    PERIODIC = 'periodic'
    PERMANENT = 'permanent'


class Event(NdbModel):
    SOURCE_CMS = 0
    SOURCE_UITDATABANK_BE = 1
    SOURCE_GOOGLE_CALENDAR = 2

    app_ids = ndb.StringProperty(indexed=True, repeated=True)
    organization_type = ndb.IntegerProperty(indexed=True)
    calendar_id = ndb.IntegerProperty(indexed=True)
    source = ndb.IntegerProperty(indexed=True, default=SOURCE_CMS)
    external_id = ndb.StringProperty(indexed=True)  # ID from source database
    external_link = ndb.TextProperty()
    title = ndb.TextProperty()
    place = ndb.TextProperty()
    description = ndb.TextProperty()
    organizer = ndb.TextProperty()
    url = ndb.TextProperty()
    calendar_type = ndb.StringProperty(choices=EventCalendarType.all())
    start_date = ndb.DateTimeProperty()  # type: datetime
    end_date = ndb.DateTimeProperty()  # type: datetime
    # only to be used in combination with calendar_type single or multiple
    periods = ndb.LocalStructuredProperty(EventPeriod, repeated=True)  # type: List[EventPeriod]
    # Only used in case calendar_type is periodic or permanent
    opening_hours = ndb.LocalStructuredProperty(EventOpeningPeriod, repeated=True)  # type: List[EventOpeningPeriod]
    deleted = ndb.BooleanProperty(indexed=True, default=False)
    media = ndb.StructuredProperty(EventMedia, repeated=True, indexed=False)  # type: List[EventMedia]

    # TODO: remove these properties after migration _005_migrate_events has ran
    first_start_date = ndb.IntegerProperty(indexed=True, default=0)
    last_start_date = ndb.IntegerProperty(indexed=True)
    start_dates = ndb.IntegerProperty(repeated=True, indexed=False)  # seconds from midnight till end
    end_dates = ndb.IntegerProperty(repeated=True, indexed=False)
    picture = ndb.BlobProperty()  # Deprecated
    picture_version = ndb.IntegerProperty(indexed=False, default=0)  # Deprecated

    @property
    def id(self):
        return self.key.id()

    @property
    def service_user(self):
        return users.User(self.key.parent().id().decode('utf-8'))

    @property
    def solution(self):
        return self.key.parent().kind()

    @classmethod
    def create_key(cls, event_id, service_user, solution):
        return ndb.Key(cls, event_id, parent=parent_ndb_key(service_user, solution))

    @classmethod
    def list_by_source_and_id(cls, event_parent_key, source, external_id):
        return cls.query(ancestor=event_parent_key) \
            .filter(cls.source == source) \
            .filter(cls.external_id == external_id)

    @classmethod
    def list_by_calendar(cls, ancestor, calendar_id):
        return cls.query(ancestor=ancestor) \
            .filter(cls.calendar_id == calendar_id) \
            .filter(cls.deleted == False) \
            .order(cls.start_date)

    @classmethod
    def list_visible_by_source(cls, service_user, solution, source):
        return cls.query(ancestor=parent_ndb_key(service_user, solution)) \
            .filter(cls.deleted == False) \
            .filter(cls.source == source)

    @classmethod
    def list_less_than_end_date(cls, date):
        return cls.query().filter(cls.end_date < date)

    @classmethod
    def list_greater_than_start_date(cls, date):
        return cls.query().filter(cls.start_date > date)

    def get_closest_occurrence(self, date):
        # type: (datetime) -> Tuple[EventDate, EventDate]
        if self.calendar_type == EventCalendarType.SINGLE:
            if self.start_date > date:
                return EventDate(datetime=self.start_date), EventDate(datetime=self.end_date)
        elif self.calendar_type == EventCalendarType.MULTIPLE:
            periods_after_date = sorted((period for period in self.periods
                                         if (period.start.date or period.start.datetime) > date),
                                        key=lambda p: p.start.date or p.start.datetime)
            if periods_after_date:
                period = periods_after_date[0]
                return period.start, period.end
        else:
            date = date if date > self.start_date else self.start_date
            if not self.opening_hours:
                # Special case - user was too lazy to specify hours -> assume it happens everyday
                if date <= self.end_date:
                    next_date = date.replace(hour=self.start_date.hour, minute=self.start_date.minute,
                                             second=self.start_date.second, microsecond=0)
                    next_date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    return EventDate(datetime=next_date), EventDate(datetime=next_date_end)
                else:
                    # Event is never happening again
                    return None, None
            day_additions = 0
            for _ in xrange(7):
                for opening_hour in self.opening_hours:
                    start_date = date.replace(hour=opening_hour.opening_hour, minute=opening_hour.opening_minute,
                                              second=0, microsecond=0) + relativedelta(days=day_additions)
                    if start_date < date:
                        continue
                    event_weekday = EventOpeningPeriod.DAY_MAPPING[start_date.weekday()]
                    if opening_hour.day == event_weekday:
                        end_date = date.replace(hour=opening_hour.close_hour, minute=opening_hour.close_minute,
                                                second=0, microsecond=0) + relativedelta(days=day_additions)
                        return EventDate(datetime=start_date), EventDate(datetime=end_date)
                day_additions += 1
        return None, None

    def get_occurrence_dates(self, current_datetime):
        # type: (datetime) -> List[Tuple[datetime, datetime]]
        # To be used for search only
        current_date = date(current_datetime.year, current_datetime.month, current_datetime.day)
        dates = []
        if self.calendar_type == EventCalendarType.SINGLE:
            if self.end_date > current_datetime:
                # Useful for 'all day' events
                if self.periods:
                    period = self.periods[0]
                    self._add_period(current_date, current_datetime, dates, period)
                else:
                    dates.append((self.start_date, self.end_date))
        elif self.calendar_type == EventCalendarType.MULTIPLE:
            for period in self.periods:
                self._add_period(current_date, current_datetime, dates, period)
        else:
            base_date = current_datetime if current_datetime > self.start_date else self.start_date
            end_of_day_of_last_day = self.end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            day_additions = 0
            if self.opening_hours:
                # Loop over every day to find all days on which the event occurs
                while True and len(dates) < 100:
                    for opening_hour in self.opening_hours:
                        start_date = base_date.replace(hour=opening_hour.opening_hour,
                                                       minute=opening_hour.opening_minute,
                                                       second=0, microsecond=0) + relativedelta(days=day_additions)
                        if start_date > end_of_day_of_last_day:
                            # No more occurrences - stop iterating
                            break
                        event_weekday = EventOpeningPeriod.DAY_MAPPING[start_date.weekday()]
                        if opening_hour.day == event_weekday:
                            end_date = base_date.replace(hour=opening_hour.close_hour, minute=opening_hour.close_minute,
                                                         second=0, microsecond=0) + relativedelta(days=day_additions)
                            if end_date <= end_of_day_of_last_day:
                                dates.append((start_date, end_date))
                    else:
                        day_additions += 1
                        continue
                    break
            else:
                # Special case - event has no opening_hours, so assume it's open every day
                # Limit this to 100 occurrences, because some people insert end dates 3000 years in the future
                # (see https://io.uitdatabank.be/event/9105dc14-602a-4a2a-b11f-68ca77f7ea8d)
                base_date = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = base_date
                day_additions = 0
                while self.end_date > start_date and len(dates) < 100:
                    start_date = base_date + relativedelta(days=day_additions)
                    end_date = start_date + relativedelta(hours=23, minutes=59, seconds=59, microseconds=999999)
                    day_additions += 1
                    dates.append((start_date, end_date))
        return dates

    def _add_period(self, current_date, current_datetime, dates, period):
        if period.start.datetime:
            if period.end.datetime > current_datetime:
                dates.append((period.start.datetime, period.end.datetime))
        else:
            if period.end.date >= current_date:
                end = period.end.date
                start = period.start.date
                start_of_day = datetime(start.year, start.month, start.day)
                end_of_day = datetime(end.year, end.month, end.day, 23, 59, 59, 999999)
                dates.append((start_of_day, end_of_day))

    @classmethod
    def list_by_calendar_type(cls, calendar_type):
        return cls.query().filter(cls.calendar_type == calendar_type)


class SolutionGoogleCredentials(NdbModel):
    email = ndb.TextProperty()
    name = ndb.TextProperty()
    gender = ndb.TextProperty()
    picture = ndb.TextProperty()
    credentials = CredentialsNDBProperty()

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, google_id):
        return ndb.Key(cls, google_id)


class SolutionCalendar(NdbModel):
    name = ndb.TextProperty()
    deleted = ndb.BooleanProperty(default=False)
    google_sync_events = ndb.BooleanProperty(default=False)
    google_credentials = ndb.TextProperty()
    google_calendar_ids = ndb.TextProperty(repeated=True)
    google_calendar_names = ndb.TextProperty(repeated=True)

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @property
    def solution(self):
        return self.key.parent().kind()

    @property
    def calendar_id(self):
        return long(self.key.id())

    @property
    def events(self):
        return Event.list_by_calendar(parent_ndb_key(self.service_user, self.solution), self.calendar_id)

    @classmethod
    def create_key(cls, calendar_id, service_user, solution):
        return ndb.Key(cls, calendar_id, parent=parent_ndb_key(service_user, solution))

    @classmethod
    def list(cls, service_user, solution, include_deleted=False):
        qry = cls.query(ancestor=parent_ndb_key(service_user, solution))
        if not include_deleted:
            qry = qry.filter(cls.deleted == False)
        return qry

    @classmethod
    def list_with_google_sync(cls):
        return cls.query().filter(cls.google_sync_events == True)

    def events_with_cursor(self, cursor, count):
        start_cursor = cursor and ndb.Cursor.from_websafe_string(cursor)
        events, cursor_, has_more = self.events.fetch_page(count, start_cursor=start_cursor)
        return cursor_ and cursor_.to_websafe_string().decode('utf-8'), events, has_more

    def get_google_credentials(self):
        if not self.google_credentials:
            return None
        credentials = SolutionGoogleCredentials.create_key(self.google_credentials).get()
        return credentials.credentials


class EventAnnouncement(NdbModel):
    image_url = ndb.TextProperty()
    color_theme = ndb.TextProperty()
    title = ndb.TextProperty()
    description = ndb.TextProperty()


class EventAnnouncements(NdbModel):
    title = ndb.TextProperty()
    title_theme = ndb.TextProperty()
    items = ndb.LocalStructuredProperty(EventAnnouncement, repeated=True)  # type: List[EventAnnouncement]

    @classmethod
    def create_key(cls):
        return ndb.Key(cls, u'EventAnnouncements')
