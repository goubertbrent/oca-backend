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

from google.appengine.ext import db

from mcfw.rpc import arguments, returns
from rogerthat.dal import parent_key
from rogerthat.rpc import users
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import OrganizationType


class CityAppProfile(db.Model):

    uitdatabank_last_query = db.IntegerProperty(indexed=False)
    uitdatabank_enabled = db.BooleanProperty(indexed=True, default=False)
    uitdatabank_secret = db.StringProperty(indexed=False)
    uitdatabank_key = db.StringProperty(indexed=False)
    uitdatabank_region = db.StringProperty(indexed=False) # deprecated since we allow multiple regions
    uitdatabank_regions = db.StringListProperty(indexed=False)
    # See https://documentatie.uitdatabank.be/content/search_api/latest/referentiegids.html for possible filters
    # properties names are for easy conversion to ndb model later
    uitdatabank_filters_key = db.StringListProperty(name='uitdatabank_filters.key', indexed=False)
    uitdatabank_filters_value = db.StringListProperty(name='uitdatabank_filters.value', indexed=False)

    # Run params in cron of CityAppSolutionGatherEvents
    gather_events_enabled = db.BooleanProperty(indexed=False, default=False)

    # Run params in cron of CityAppSolutionEventsUitdatabank
    run_time = db.IntegerProperty(indexed=False)

    review_news = db.BooleanProperty(indexed=False)

    EVENTS_ORGANIZATION_TYPES = [OrganizationType.NON_PROFIT, OrganizationType.PROFIT, OrganizationType.CITY,
                                 OrganizationType.EMERGENCY]

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    @returns(db.Key)
    @arguments(service_user=users.User)
    def create_key(service_user):
        return db.Key.from_path(CityAppProfile.kind(), 'profile', parent=parent_key(service_user, SOLUTION_COMMON))
