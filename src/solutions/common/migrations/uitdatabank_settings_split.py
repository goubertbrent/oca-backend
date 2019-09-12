# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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

from rogerthat.bizz.job import run_job
from rogerthat.rpc import users
from solutions.common.models.cityapp import CityAppProfile, UitdatabankSettings


def job():
    run_job(_qry, [], _worker, [])


def _qry():
    return CityAppProfile.all()


def _worker(city_app_profile):
    if not city_app_profile.uitdatabank_enabled:
        return

    s = UitdatabankSettings(key=UitdatabankSettings.create_key(city_app_profile.service_user))
    s.enabled = True
    if city_app_profile.uitdatabank_secret:
        s.version = UitdatabankSettings.VERSION_2
        s.params = {
            u'key': city_app_profile.uitdatabank_key,
            u'secret': city_app_profile.uitdatabank_secret,
            u'regions': city_app_profile.uitdatabank_regions,
            u'filters': []
        }
        for key, value in zip(city_app_profile.uitdatabank_filters_key, city_app_profile.uitdatabank_filters_value):
            s.params[u'filters'].append({
                u'key': key,
                u'value': value
            })
    else:
        s.version = UitdatabankSettings.VERSION_1
        s.params = {
            u'key': city_app_profile.uitdatabank_key,
            u'region': city_app_profile.uitdatabank_regions[0]
        }
    s.cron_run_time = city_app_profile.run_time
    s.cron_sync_time = city_app_profile.uitdatabank_last_query
    s.put()
