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

import base64
import httplib

from google.appengine.ext.webapp import blobstore_handlers
from rogerthat.consts import DAY
from rogerthat.models import Image
from rogerthat.rpc import users
import webapp2


class UserAwareRequestHandler(webapp2.RequestHandler):

    def set_user(self):
        user = self.request.headers.get("X-MCTracker-User", None)
        password = self.request.headers.get("X-MCTracker-Pass", None)
        if not user or not password:
            return False
        return users.set_json_rpc_user(base64.decodestring(user), base64.decodestring(password))


class ViewImageHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, image_id):
        try:
            image_id = long(image_id)
        except ValueError:
            self.error(httplib.NOT_FOUND)
            return
        image = Image.get_by_id(image_id)
        if not image:
            self.error(httplib.NOT_FOUND)
            return
        self.response.cache_control = 'public'
        self.response.cache_expires(DAY * 30)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.headers['Content-Disposition'] = 'inline; filename=%d.jpg' % image_id
        self.response.write(image.blob)
