# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

from datetime import date
from dateutil.relativedelta import relativedelta

import mc_unittest

from rogerthat.rpc import users
from rogerthat.models import UserProfile
from rogerthat.models.news import NewsItem
from rogerthat.utils import get_epoch_from_datetime, now

class TestNewsItem(mc_unittest.TestCase):

    def test_news_item_target_audience(self):
        today = date.today()
        date_old = today + relativedelta(years=-40)
        date_ancient = today + relativedelta(years=-500)
        date_young = today + relativedelta(years=-10)

        empty_profile = UserProfile(birthdate=None, gender=None)
        profile_old_male = UserProfile(birthdate=get_epoch_from_datetime(date_old),
                                       gender=UserProfile.GENDER_MALE)
        profile_old_female = UserProfile(birthdate=get_epoch_from_datetime(date_old),
                                         gender=UserProfile.GENDER_FEMALE)
        profile_ancient_female = UserProfile(birthdate=get_epoch_from_datetime(date_ancient),
                                             gender=UserProfile.GENDER_FEMALE)
        young_female = UserProfile(birthdate=get_epoch_from_datetime(date_young),
                                   gender=UserProfile.GENDER_FEMALE)

        news_item0 = NewsItem(sticky=False,
                              sender=users.User('hello@mail.com'),
                              app_ids=['rogerthat'],
                              timestamp=now(),
                              rogered=False,
                              target_audience_enabled=False)

        self.assertTrue(news_item0.match_target_audience(profile_old_male))
        self.assertTrue(news_item0.match_target_audience(young_female))
        self.assertTrue(news_item0.match_target_audience(empty_profile))

        news_item1 = NewsItem(sticky=False,
                              sender=users.User('hello@mail.com'),
                              app_ids=['rogerthat'],
                              timestamp=now(),
                              rogered=False,
                              target_audience_enabled=True,
                              target_audience_min_age=0,
                              target_audience_max_age=100,
                              target_audience_gender=UserProfile.GENDER_FEMALE)

        self.assertFalse(news_item1.match_target_audience(empty_profile))
        self.assertFalse(news_item1.match_target_audience(profile_old_male))
        self.assertTrue(news_item1.match_target_audience(profile_old_female))
        self.assertFalse(news_item1.match_target_audience(profile_ancient_female))
        self.assertTrue(news_item1.match_target_audience(young_female))

        news_item2 = NewsItem(sticky=False,
                              sender=users.User('hello@mail.com'),
                              app_ids=['rogerthat'],
                              timestamp=now(),
                              rogered=False,
                              target_audience_enabled=True,
                              target_audience_min_age=18,
                              target_audience_max_age=99,
                              target_audience_gender=UserProfile.GENDER_MALE_OR_FEMALE)

        self.assertFalse(news_item2.match_target_audience(empty_profile))
        self.assertTrue(news_item2.match_target_audience(profile_old_male))
        self.assertTrue(news_item2.match_target_audience(profile_old_female))
        self.assertFalse(news_item2.match_target_audience(profile_ancient_female))
        self.assertFalse(news_item2.match_target_audience(young_female))
