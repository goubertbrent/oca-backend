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

from datetime import datetime

from dateutil.relativedelta import relativedelta
from google.appengine.ext import ndb
import webapp2

from mcfw.utils import chunks
from rogerthat.models import OAuthState
from rogerthat.models.auth.acm import ACMLoginState, ACMLogoutState


class RemoveStatesHandler(webapp2.RequestHandler):
    def get(self):
        today = datetime.now()
        yesterday = today - relativedelta(days=1)

        for cls in (OAuthState, ACMLoginState, ACMLogoutState):
            to_delete = cls.list_before_date(yesterday).fetch(keys_only=True)
            for chunk in chunks(to_delete, 500):
                ndb.delete_multi(chunk)