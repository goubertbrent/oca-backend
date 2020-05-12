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

import json

from oauth2client.appengine import OAuth2Decorator
import webapp2

from solution_server_settings.consts import GMB_OAUTH_CLIENT_ID,\
    GMB_OAUTH_CLIENT_SECRET


discoveryServiceUrlV4 = 'https://developers.google.com/my-business/samples/mybusiness_google_rest_v4.json'
discoveryServiceUrlV4P5 = 'https://developers.google.com/my-business/samples/mybusiness_google_rest_v4p5.json'


gmbOauthDecorator = OAuth2Decorator(
    client_id=GMB_OAUTH_CLIENT_ID,
    client_secret=GMB_OAUTH_CLIENT_SECRET,
    scope=u'https://www.googleapis.com/auth/business.manage',
    callback_path=u'/admin/gmb/oauth2callback', )


class GoogleMyBusinessHandler(webapp2.RequestHandler):

    @gmbOauthDecorator.oauth_required
    def get(self):
        from googleapiclient.discovery import build
        credentials = gmbOauthDecorator.credentials  # type: Credentials
        http_auth = credentials.authorize(gmbOauthDecorator.http())
        q = self.request.get('q', 'accounts')
        if q == 'accounts':
            service = build('mybusiness', 'v4', http=http_auth, discoveryServiceUrl=discoveryServiceUrlV4P5)
            r = service.accounts().list().execute()
        elif q == 'locations':
            service = build('mybusiness', 'v4', http=http_auth, discoveryServiceUrl=discoveryServiceUrlV4P5)
            parent = self.request.get('parent')
            r = service.accounts().locations().list(parent=parent).execute()
        elif q == 'questions':
            service = build('mybusiness', 'v4', http=http_auth, discoveryServiceUrl=discoveryServiceUrlV4P5)
            parent = self.request.get('parent')
            r = service.accounts().locations().questions().list(parent=parent).execute()
        elif q == 'reviews':
            service = build('mybusiness', 'v4', http=http_auth, discoveryServiceUrl=discoveryServiceUrlV4P5)
            parent = self.request.get('parent')
            r = service.accounts().locations().reviews().list(parent=parent).execute()
        elif q == 'categories':
            service = build('mybusiness', 'v4', http=http_auth, discoveryServiceUrl=discoveryServiceUrlV4)
            regionCode = self.request.get('regionCode')
            languageCode = self.request.get('languageCode')
            r = service.categories().list(regionCode=regionCode, languageCode=languageCode).execute()
        else:
            r = {}

        self.response.headers['Content-Type'] = 'text/json'
        self.response.write(json.dumps(r))
