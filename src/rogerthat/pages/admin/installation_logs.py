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

import os
import time

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.dal.registration import get_installations, get_installation_logs_by_installation, \
    get_mobiles_and_profiles_for_installations
from rogerthat.to.installation import DeprecatedInstallationsTO

DAY = 86400

class InstallationLogsHandler(webapp.RequestHandler):


    def _epoch_to_str(self, epoch):
        split = time.ctime(epoch).split(" ")
        while "" in split:
            split.remove("")
        split.remove(split[3])  # Removing timestamp
        return " ".join(split)

    def get(self):
        offset = int(self.request.GET.get("offset", 0))  # go back <offset> days in the past
        current_day = int(time.time() / DAY) - offset
        args = {"offset": offset,
                "current_day":self._epoch_to_str(current_day * DAY),
                "next_url":"/mobiadmin/installation_logs?offset=%s" % (offset - 1) if offset else "",
                "back_url":"/mobiadmin/installation_logs?offset=%s" % (offset + 1)}
        path = os.path.join(os.path.dirname(__file__), 'installation_logs.html')
        self.response.out.write(template.render(path, args))


@rest('/mobiadmin/installation_logs/load', 'get', silent_result=True)
@returns(DeprecatedInstallationsTO)
@arguments(offset=int, cursor=unicode)
def get_installation_logs(offset, cursor):
    if not cursor:
        cursor = None
    current_day = int(time.time() / DAY) - offset
    min_timestamp = current_day * DAY
    max_timestamp = min_timestamp + DAY
    installations, new_cursor = get_installations(min_timestamp, max_timestamp, cursor, 30)
    # not very efficient... Executes 30 queries simultaneously
    logs = {installation.key(): get_installation_logs_by_installation(installation) for installation in
            installations}
    mobiles, profiles = get_mobiles_and_profiles_for_installations(installations)
    return DeprecatedInstallationsTO.from_model(offset, new_cursor, installations, logs, mobiles, profiles)
