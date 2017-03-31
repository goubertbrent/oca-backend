# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

import base64
import logging
import urllib
import urllib2

from rogerthat.rpc import users
from rogerthat.rpc.models import TempBlob
from rogerthat.service.api.system import put_avatar
from google.appengine.api import images
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from solutions.djmatic import JUKEBOX_SERVER_API_URL
from solutions.djmatic.dal import get_djmatic_profile

@rest("/djmatic/settings/avatar/post", "post")
@returns(unicode)
@arguments(tmp_avatar_key=str, x1=(float, int), y1=(float, int), x2=(float, int), y2=(float, int))
def put_djmatic_avatar_handler(tmp_avatar_key, x1, y1, x2, y2):
    x1 = float(x1)
    x2 = float(x2)
    y1 = float(y1)
    y2 = float(y2)
    try:
        tb = TempBlob.get(tmp_avatar_key)
        # First cut the image selected in the web page
        img = images.Image(str(tb.blob))
        logging.debug("DJ-Matic put avatar X1: %s X2: %s Y1: %s Y2: %s" % (x1, x2, y1, y2))
        img.crop(x1, y1, x2, y2)
        image = img.execute_transforms()
        # Reload the image in a new image object to get the exact height and width
        img_control = images.Image(image)
        img_control.im_feeling_lucky()  # We need to do this to get the widht and height
        img_control.execute_transforms()
        # Resize the image to the heigth of the cropped image, and crop leftovers away (floating pixels)
        h = min(4000, img_control.height)  # max 4000 wide/high
        img.resize(h, h, True)
        image = img.execute_transforms()


        # To make sure png image is smaller then 1MB
        size = 100
        orig_width = img.width
        orig_height = img.height
        orig_image = image
        base64_image = base64.b64encode(image)
        while len(base64_image) > (1024 * 1024 - 100 * 1024):
            size -= size / 10
            img = images.Image(orig_image)
            img.resize(orig_width * size / 100, orig_height * size / 100)
            image = img.execute_transforms()
            base64_image = base64.b64encode(image)

        logging.debug("DJ-Matic put avatar H: %s W: %s" % (img.height, img.width))
        put_avatar(base64_image)

        service_user = users.get_current_user()
        djmatic_profile = get_djmatic_profile(service_user)

        url = JUKEBOX_SERVER_API_URL
        values = {'method' : 'player.updateAvatar',
                  'player_id' : djmatic_profile.player_id,
                  'secret' : djmatic_profile.secret,
                  'image' : base64_image }

        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        the_page = response.read()
        logging.info("Response PHP: %s" % the_page)

    except Exception, e:
        logging.exception(e)
        return e.message
