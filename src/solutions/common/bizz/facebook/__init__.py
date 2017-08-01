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
import StringIO

import facebook

from mcfw.rpc import returns, arguments
from mcfw.utils import chunks

from solution_server_settings import get_solution_server_settings


@returns(tuple)
@arguments(domain=unicode)
def get_facebook_app_info(domain):
    settings = get_solution_server_settings()
    apps = settings.facebook_apps

    for host, app_id, app_secret in chunks(apps, 3):
        if host == domain.lower().strip():
            return app_id, app_secret


@returns()
@arguments(access_token=unicode, message=unicode, image=str)
def post_to_facebook(access_token, message, image=None):
    """
    Post to facebook.

    Args:
        access_token (unicode): user or page access token
        message (unicode)
        image (str): image content
    """
    fb = facebook.GraphAPI(access_token)

    try:
        if image:
            image_source = StringIO.StringIO(image)
            fb.put_photo(image=image_source, message=message)
        else:
            fb.put_wall_post(message)
    except facebook.GraphAPIError:
        logging.error('Post to facebook failed', exc_info=True, _suppress=False)


@returns(unicode)
@arguments(domain=unicode, access_token=unicode)
def extend_access_token(domain, access_token):
    try:
        app_id, app_secret = get_facebook_app_info(domain)
    except ValueError:
        raise ValueError('No facebook app is linked to %s' % domain)

    fb = facebook.GraphAPI(access_token)
    extended_token = fb.extend_access_token(app_id, app_secret)['access_token']

    return extended_token
