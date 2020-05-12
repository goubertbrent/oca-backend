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

import logging
import pprint
import time

from rogerthat.models import App
from rogerthat.settings import get_server_settings
from rogerthat.utils import now, send_mail
import webapp2


class ApnExpirationCheckHandler(webapp2.RequestHandler):

    def get(self):
        expired_apps = [(app.app_id, time.ctime(app.apple_push_cert_valid_until))
                        for app in App.all() \
                            .filter('apple_push_cert_valid_until !=', None) \
                            .filter('apple_push_cert_valid_until <', now() + 60 * 86400) \
                            .order('apple_push_cert_valid_until')]
        if expired_apps:
            expired_apps_str = pprint.pformat(expired_apps)
            settings = get_server_settings()
            send_mail(settings.dashboardEmail,
                      settings.supportWorkers,
                      "There are APN certs that are about to expire",
                      "The following APN certs are about to expire:\n%s" % expired_apps_str)
            logging.error("The following APN certs are about to expire:\n%s" % expired_apps_str)
