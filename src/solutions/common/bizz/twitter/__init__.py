# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import logging

from google.appengine.api import urlfetch
from twitter import *

from mcfw.rpc import returns, arguments
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.to.messaging import AttachmentTO
from rogerthat.utils import oauth
from rogerthat.utils.channel import send_message
from solutions.common.dal import get_solution_settings
from solution_server_settings import get_solution_server_settings


try:
    import urllib.parse as urllib_parse
    from urllib.parse import urlencode
except ImportError:
    import urllib2 as urllib_parse
    from urllib import urlencode
CALLBACK_URL = '%s/unauthenticated/osa/callback/twitter?%s'

@returns(bool)
@arguments(service_user=users.User, message=unicode, attachments=[AttachmentTO])
def post_to_twitter(service_user, message, attachments):
    sln_settings = get_solution_settings(service_user)
    if not sln_settings.twitter_oauth_token:
        return False
    solution_server_settings = get_solution_server_settings()
    try:
        auth = OAuth(sln_settings.twitter_oauth_token, sln_settings.twitter_oauth_token_secret, \
                     solution_server_settings.twitter_app_key, solution_server_settings.twitter_app_secret)
        t = Twitter(auth=auth)
        media_ids = []
        if attachments:
            t_up = Twitter(domain='upload.twitter.com', auth=auth)
            for attachment in attachments:
                try:
                    try:
                        result = urlfetch.fetch(attachment.download_url, deadline=15)
                    except urlfetch.DownloadError:
                        continue

                    if result.status_code != 200:
                        continue

                    img_str = result.content
                    img_id = t_up.media.upload(media=img_str)["media_id_string"]
                    media_ids.append(img_id)
                except:
                    logging.warn('upload media twitter failed', exc_info=True)

        if media_ids:
            t.statuses.update(status=message, media_ids=",".join(media_ids))
        else:
            t.statuses.update(status=message)
        return True
    except:
        logging.error('Update twitter status failed', exc_info=True)
        return False

@returns(unicode)
@arguments(service_user=users.User)
def get_twitter_auth_url(service_user):
    server_settings = get_server_settings()
    solution_server_settings = get_solution_server_settings()
    client = oauth.TwitterClient(solution_server_settings.twitter_app_key, solution_server_settings.twitter_app_secret, \
                                 CALLBACK_URL % (server_settings.baseUrl, urlencode({"s": service_user.email()})))
    auth_url = client.get_authorization_url()
    return auth_url

@returns(unicode)
@arguments(service_user=users.User)
def twitter_logout(service_user):
    sln_settings = get_solution_settings(service_user)
    sln_settings.twitter_oauth_token = None
    sln_settings.twitter_oauth_token_secret = None
    sln_settings.twitter_username = None
    put_and_invalidate_cache(sln_settings)
    send_message(service_user, u"solutions.common.twitter.updated", username=None)
