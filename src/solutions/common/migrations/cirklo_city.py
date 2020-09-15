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

from solutions.common.integrations.cirklo.models import CirkloCity, SignupMails, SignupLanguageProperty


def migrate(dry_run=True):
    to_put = []
    for city in CirkloCity.query():  # type: CirkloCity
        city.signup_mail = None
        if city.signup_mails:
            city.signup_mail = SignupMails()
            city.signup_mail.accepted = SignupLanguageProperty(nl=city.signup_mails.accepted)
            city.signup_mail.denied = SignupLanguageProperty(nl=city.signup_mails.denied)
            to_put.append(city)
    if dry_run:
        return 'Dry run', to_put
    ndb.put_multi(to_put)
    return 'Migrated', to_put
