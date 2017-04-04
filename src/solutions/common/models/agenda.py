# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.3@@

from rogerthat.dal import parent_key
from rogerthat.rpc import users
from rogerthat.utils import now
from rogerthat.utils.service import get_service_user_from_service_identity_user, \
    get_identity_from_service_identity_user
from google.appengine.ext import db
from oauth2client.appengine import CredentialsProperty
from solutions.common.models.properties import SolutionUserProperty


class Event(db.Model):
    SOURCE_CMS = 0
    SOURCE_UITDATABANK_BE = 1
    SOURCE_GOOGLE_CALENDAR = 2
    SOURCE_SCRAPER = 3

    calendar_id = db.IntegerProperty(indexed=True)

    source = db.IntegerProperty(indexed=True, default=SOURCE_CMS)
    external_id = db.StringProperty(indexed=True)  # ID from source database
    external_link = db.StringProperty(indexed=False)

    title = db.StringProperty(indexed=False)
    place = db.StringProperty(indexed=False)
    description = db.TextProperty()
    organizer = db.StringProperty(indexed=False)
    url = db.StringProperty(indexed=False)

    first_start_date = db.IntegerProperty(indexed=True, default=0)
    last_start_date = db.IntegerProperty(indexed=True)
    start_dates = db.ListProperty(int, indexed=False)  # seconds from midnight till end
    end_dates = db.ListProperty(int, indexed=False)
    deleted = db.BooleanProperty(indexed=True, default=False)
    picture = db.BlobProperty()
    picture_version = db.IntegerProperty(indexed=False, default=0)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def solution(self):
        return self.parent_key().kind()

    @property
    def guests(self):
        return EventGuest.all().ancestor(self.key())

    def guests_count(self, status):
        return EventGuest.all(keys_only=True).ancestor(self.key()).filter("status =", status).count(None)

    @classmethod
    def get_future_event_keys(cls, current_date):
        return db.Query(cls, keys_only=True).filter('deleted =', False).filter('last_start_date >', current_date)

    def get_first_event_date(self):
        if len(self.start_dates) > 1:
            first_start_date = self.start_dates[-1]
            now_ = now()
            for start_date in self.start_dates:
                if start_date > now_:
                    first_start_date = start_date
                    break
            return first_start_date
        else:
            return self.start_dates[0]

class EventReminder(db.Model):
    STATUS_PENDING = 1
    STATUS_REMINDED = 2

    service_identity_user = db.UserProperty(indexed=True)
    human_user = db.UserProperty(indexed=True)  # app_user
    event_id = db.IntegerProperty(indexed=True)
    event_start_epoch = db.IntegerProperty(indexed=True)
    remind_before = db.IntegerProperty(indexed=True)
    status = db.IntegerProperty(required=True, default=STATUS_PENDING)

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)


class SolutionCalendarAdmin(db.Model):
    timestamp = db.IntegerProperty(indexed=False)
    app_user = db.UserProperty(indexed=True)

    @property
    def calendar_key(self):
        return self.parent_key()

    @staticmethod
    def createKey(app_user, solutions_calendar_key):
        return db.Key.from_path(SolutionCalendarAdmin.kind(), app_user.email(), parent=solutions_calendar_key)

class SolutionCalendarGoogleSync(db.Model):
    google_calendar_keys = db.StringListProperty(indexed=False)

    @property
    def service_user(self):
        return users.User(self.key().name())

class SolutionGoogleCredentials(db.Model):
    email = db.StringProperty(indexed=False)
    name = db.StringProperty(indexed=False)
    gender = db.StringProperty(indexed=False)
    picture = db.StringProperty(indexed=False)
    credentials = CredentialsProperty(indexed=False)

    @property
    def id(self):
        return self.key().name()

    @staticmethod
    def createKey(google_id):
        return db.Key.from_path(SolutionGoogleCredentials.kind(), google_id)

class SolutionCalendar(db.Model):
    name = db.StringProperty(indexed=False)
    deleted = db.BooleanProperty(indexed=True, default=False)
    connector_qrcode = db.StringProperty(indexed=False)
    broadcast_enabled = db.BooleanProperty(indexed=True, default=False)
    google_sync_events = db.BooleanProperty(indexed=True, default=False)

    google_credentials = db.StringProperty(indexed=False)
    google_calendar_ids = db.StringListProperty(indexed=False, default=[])
    google_calendar_names = db.StringListProperty(indexed=False, default=[])

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def solution(self):
        return self.parent_key().kind()

    @property
    def calendar_id(self):
        return self.key().id()

    def get_admins(self):
        return SolutionCalendarAdmin.all().ancestor(self.key())

    @property
    def events(self):
        return Event.all().ancestor(parent_key(self.service_user, self.solution)).filter("calendar_id =", self.calendar_id).filter("deleted =", False)

    def events_with_cursor(self, cursor, count):
        qry = Event.all().with_cursor(cursor).ancestor(parent_key(self.service_user, self.solution)).filter("calendar_id =", self.calendar_id).filter("deleted =", False).order("first_start_date")
        events = qry.fetch(count)
        cursor_ = qry.cursor()
        has_more = False
        if len(events) != 0:
            qry.with_cursor(cursor_)
            if len(qry.fetch(1)) > 0:
                has_more = True

        return unicode(cursor_), events, has_more

    def get_google_credentials(self):
        if not self.google_credentials:
            return None
        sgc = SolutionGoogleCredentials.get(SolutionGoogleCredentials.createKey(self.google_credentials))
        return sgc.credentials


class EventGuest(db.Model):
    STATUS_GOING = 1
    STATUS_MAYBE = 2
    STATUS_NOT_GOING = 3

    # as in translation keys
    STATUS_KEYS = {
        STATUS_GOING: u'Going',
        STATUS_MAYBE: u'Maybe',
        STATUS_NOT_GOING: u'Not going'
    }

    guest = SolutionUserProperty(indexed=False)
    timestamp = db.IntegerProperty(indexed=False)
    status = db.IntegerProperty(indexed=True)

    chat_key = db.StringProperty(indexed=False)

    @property
    def status_str(self):
        return EventGuest.STATUS_KEYS.get(self.status)

    @property
    def app_user(self):
        return users.User(self.key().name())

    @staticmethod
    def createKey(app_user, event_key):
        return db.Key.from_path(EventGuest.kind(), app_user.email(), parent=event_key)
