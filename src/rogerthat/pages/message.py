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

import datetime
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import cloudstorage
from mcfw.properties import azzert
from rogerthat.bizz import gcs
from rogerthat.consts import ROGERTHAT_ATTACHMENTS_BUCKET
from rogerthat.rpc.users import get_current_user
from rogerthat.templates import render
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import hash_user_identifier
from rogerthat.utils.app import get_human_user_from_app_user
from rogerthat.utils.channel import broadcast_via_iframe_result
from rogerthat.utils.crypto import md5_hex

_BASE_DIR = os.path.dirname(__file__)


class MessageHandler(webapp.RequestHandler):
    def get(self):
        user_agent = self.request.environ['HTTP_USER_AGENT']
        mobile = "Android" in user_agent or "iPhone" in user_agent or 'iPad' in user_agent or 'iPod' in user_agent
        message = self.request.get("message", "Thank you for using Rogerthat!")
        path = os.path.join(_BASE_DIR, 'message.html')
        self.response.out.write(template.render(path, {'message': message, "mobile": mobile}))


class MessageHistoryHandler(webapp.RequestHandler):
    def get(self):
        member_email = self.request.GET.get('member')
        azzert(member_email)

        #        user = users.get_current_user()
        #        member = users.User(member_email)
        #        TODO: check friend relation between user & member

        params = dict(container_id='messageHistory_%s' % md5_hex(member_email), query_param=member_email,
                      query_type='message_history')
        self.response.out.write(render('message_query', [DEFAULT_LANGUAGE], params, 'web'))


class PhotoUploadUploadHandler(webapp.RequestHandler):
    def post(self):
        f = self.request.POST.get('file')  # type: FieldStorage
        date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        user = get_human_user_from_app_user(get_current_user())
        user_hash = hash_user_identifier(user)
        filename = '%s/web/photo_upload/%s/%s_%s' % (ROGERTHAT_ATTACHMENTS_BUCKET, user_hash, date, f.filename)
        with cloudstorage.open(filename, 'w', content_type=f.type) as gcs_file:
            gcs_file.write(f)
        self.response.out.write(broadcast_via_iframe_result(u'rogerthat.messaging.photo_upload_done',
                                                            downloadUrl=gcs.get_serving_url(filename)))
