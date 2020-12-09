# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
from google.appengine.ext import ndb

from solutions.common.models import SolutionRssScraperSettings


def migrate_rss_links(dry_run=True):
    to_put = []
    for settings in SolutionRssScraperSettings.query():  # type: SolutionRssScraperSettings
        for link_settings in settings.rss_links:
            link_settings.notify = settings.notify
        to_put.append(settings)
    if dry_run:
        return 'To update: %s' % len(to_put)
    ndb.put_multi(to_put)
