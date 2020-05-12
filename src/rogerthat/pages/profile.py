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

import base64
import logging

from google.appengine.api import images
import webapp2

from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from rogerthat.bizz.profile import UNKNOWN_AVATAR
from rogerthat.dal.profile import get_avatar_by_id, get_service_or_user_profile
from rogerthat.rpc import users


@returns(str)
@arguments(avatar_id=int, size=int)
def get_avatar(avatar_id, size=150):
    if avatar_id <= 0:
        return UNKNOWN_AVATAR
    avatar = get_avatar_by_id(avatar_id)
    if avatar and avatar.picture:
        picture = str(avatar.picture)
        img = images.Image(picture)
        if img.width > size or img.height > size:
            img.resize(size, size)
            return img.execute_transforms(output_encoding=img.format)
        else:
            return picture
    else:
        return UNKNOWN_AVATAR


@cached(1, lifetime=86400, request=False, memcache=True)
@returns(str)
@arguments(avatar_id=int, size=int)
def get_avatar_cached(avatar_id, size=150):
    return get_avatar(avatar_id, size)


class GetMyAvatarHandler(webapp2.RequestHandler):

    def get(self):
        user_email = self.request.get('user')
        if not user_email:
            self.error(500)
            logging.error("user not provided")
            return
        user = users.User(user_email)
        if user != users.get_current_user():
            session = users.get_current_session()
            if not session.has_access(user_email):
                self.error(500)
                logging.error("Logged in user %s does not have access to %s", session.user, user_email)
                return
        profile = get_service_or_user_profile(user)
        self.response.headers['Content-Type'] = "image/png"
        avatarId = -1 if not profile or not profile.avatarId else profile.avatarId
        self.response.out.write(get_avatar_cached(avatarId))


class GetCachedAvatarHandler(webapp2.RequestHandler):

    def get(self, avatar_id):
        if not avatar_id:
            self.error(404)
            return

        self.response.headers['Cache-Control'] = "public, max-age=86400"
        self.response.headers['Access-Control-Allow-Origin'] = "*"
        avatar = get_avatar_cached(int(avatar_id))
        if self.request.get('base64'):
            self.response.headers['Content-Type'] = "text/plain"
            self.response.out.write(base64.b64encode(avatar))
        else:
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(avatar)


class GetAvatarHandler(webapp2.RequestHandler):

    def get(self, avatar_id):
        if not avatar_id:
            self.error(404)
            return

        size = self.request.get('s', '150')
        self.response.headers['Content-Type'] = "image/png"
        self.response.out.write(get_avatar(int(avatar_id), int(size)))
