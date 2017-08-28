# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
import logging
import urllib
import urllib2

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.service.api.system import put_avatar
from solutions.djmatic import JUKEBOX_SERVER_API_URL
from solutions.djmatic.dal import get_djmatic_profile


@rest('/djmatic/settings/avatar', 'post', silent=True)
@returns(unicode)
@arguments(image=unicode)
def rest_put_djmatic_avatar_handler(image):
    try:
        _meta, img_b64 = image.split(',')
        put_avatar(img_b64)
        service_user = users.get_current_user()
        djmatic_profile = get_djmatic_profile(service_user)

        values = {
            'method': 'player.updateAvatar',
            'player_id': djmatic_profile.player_id,
            'secret': djmatic_profile.secret,
            'image': img_b64
        }
        data = urllib.urlencode(values)
        req = urllib2.Request(JUKEBOX_SERVER_API_URL, data)
        response = urllib2.urlopen(req)
        the_page = response.read()
        logging.info('Response from DJMatic: %s', the_page)

    except Exception as e:
        logging.exception(e)
        return e.message
