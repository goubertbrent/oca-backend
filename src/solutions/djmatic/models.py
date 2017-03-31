# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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
# @@license_version:1.2@@

import datetime
import time

from rogerthat.dal import parent_key
from rogerthat.models import ServiceIdentityStatistic, ServiceIdentity
from rogerthat.rpc import users
from rogerthat.utils.service import create_service_identity_user
from google.appengine.ext import db
from mcfw.rpc import arguments, returns
from solutions.common.dal import get_solution_settings
from solutions.djmatic import SOLUTION_DJMATIC


class DjmaticOverviewLog(db.Model):
    timestamp = db.IntegerProperty()
    email = db.StringProperty(indexed=True)
    player_id = db.StringProperty(indexed=True)
    description = db.StringProperty(indexed=False, multiline=True)

    @property
    def time(self):
        return time.strftime("%a %d %b %Y\n%H:%M:%S GMT", time.localtime(self.timestamp))


class DjMaticProfile(db.Model):
    STATUS_CREATED = 0
    STATUS_TRIAL = 1
    STATUS_DEMO = 2
    STATUS_FULL = 3
    STATUS_LIMITED = 4

    STATUS_STRINGS = {STATUS_CREATED: u"Created",
                      STATUS_TRIAL: u"Trial",
                      STATUS_DEMO: u"Demo",
                      STATUS_FULL: u"Full",
                      STATUS_LIMITED: u"Limited"}

    PLAYER_TYPE_DJMATIC = 0
    PLAYER_TYPE_BOXY = 1

    secret = db.StringProperty(indexed=False)
    player_id = db.StringProperty(indexed=True)
    jukebox_branding_hash = db.StringProperty(indexed=False)  # rogerthat branding hash
    connect_qr_img_url = db.StringProperty(indexed=False)
    player_type = db.IntegerProperty(indexed=False)
    creation_time = db.IntegerProperty(indexed=True)
    status = db.IntegerProperty(indexed=True)
    start_trial_time = db.IntegerProperty(indexed=True)
    status_history = db.ListProperty(int, indexed=False)
    status_history_epoch = db.ListProperty(long, indexed=False)

    @property
    def type(self):
        return "DJ-Matic" if self.player_type == DjMaticProfile.PLAYER_TYPE_DJMATIC else "Boxy"

    @property
    def name(self):
        settings = get_solution_settings(self.service_user)
        return settings.name

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def days_created(self):
        if self.creation_time:
            return (datetime.date.today() - datetime.date.fromtimestamp(self.creation_time)).days
        else:
            return 0

    @property
    def days_created_date(self):
        if self.creation_time:
            return datetime.date.fromtimestamp(self.creation_time)
        else:
            return datetime.date.today()

    @property
    def days(self):
        if self.start_trial_time:
            return (datetime.date.today() - datetime.date.fromtimestamp(self.start_trial_time)).days
        else:
            return 0

    @property
    def days_date(self):
        if self.start_trial_time:
            return datetime.date.fromtimestamp(self.start_trial_time)
        else:
            return datetime.date.today()

    @property
    def connected_users(self):
        sid_key = ServiceIdentityStatistic.create_key(create_service_identity_user(self.service_user,
                                                                               identity=ServiceIdentity.DEFAULT))
        sid = db.get(sid_key)
        if sid:
            return sid.number_of_users
        else:
            return 0

    @staticmethod
    def status_string(status):
        return DjMaticProfile.STATUS_STRINGS.get(status)

    @staticmethod
    @returns(db.Key)
    @arguments(service_user=users.User)
    def create_key(service_user):
        return db.Key.from_path(DjMaticProfile.kind(), 'profile', parent=parent_key(service_user, SOLUTION_DJMATIC))

class JukeboxAppBranding(db.Model):
    blob = db.BlobProperty(indexed=False)

    @staticmethod
    def create_key():
        return db.Key.from_path(JukeboxAppBranding.kind(), u'jukebox_branding')
