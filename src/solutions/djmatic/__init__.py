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

from rogerthat.consts import DEBUG
from rogerthat.rpc import users

SOLUTION_DJMATIC = u"djmatic"

DEFAULT_LANGUAGES = [u'en']

JUKEBOX_SERVER_API_URL = u'%s/api.php' % ('http://jabber.mobicage.com/jukebox-server' if DEBUG else 'https://mobicage.dj-matic.com')
