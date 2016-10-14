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

import webapp2

from rogerthat.dal import put_and_invalidate_cache
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.utils import oauth, urlencode
from rogerthat.utils.channel import send_message
from rogerthat.utils.oauth import AuthToken
from solutions.common.bizz.twitter import CALLBACK_URL
from solutions.common.dal import get_solution_settings
from solution_server_settings import get_solution_server_settings


class SolutionsCallbackTwitterHandler(webapp2.RequestHandler):

    def get(self):
        service_user_email = self.request.get("s")
        service_user = users.User(service_user_email)
        denied = self.request.get("denied")
        if denied:
            self.response.out.write("""<html>
    <body><h1>Twitter login cancelled, you can close this window now.</h1></body>
    <script>self.close();</script>
</html>""")
        else:
            oauth_token = self.request.get("oauth_token")
            oauth_verifier = self.request.get("oauth_verifier")

            logging.info("service_user_email: %s", service_user_email)
            logging.info("oauth_token: %s", oauth_token)
            logging.info("oauth_verifier: %s", oauth_verifier)

            key = AuthToken.key_name(oauth.TWITTER, oauth_token)
            auth_model = AuthToken.get_by_key_name(key)
            if auth_model:
                server_settings = get_server_settings()
                solution_server_settings = get_solution_server_settings()
                client = oauth.TwitterClient(solution_server_settings.twitter_app_key,
                                             solution_server_settings.twitter_app_secret,
                                             CALLBACK_URL % (server_settings.baseUrl, urlencode({"s": service_user.email()})))

                r = client.get_user_info(oauth_token, oauth_verifier, True)

                sln_settings = get_solution_settings(service_user)
                if sln_settings:
                    sln_settings.twitter_oauth_token = r["token"]
                    sln_settings.twitter_oauth_token_secret = r["secret"]
                    sln_settings.twitter_username = r["username"]
                    put_and_invalidate_cache(sln_settings)
                    send_message(service_user, u"solutions.common.twitter.updated", username=r["username"])

            self.response.out.write("""<html>
    <body><h1>witter login success, you can close this window now.</h1></body>
    <script>self.close();</script>
</html>""")
