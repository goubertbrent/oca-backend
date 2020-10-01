# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
# @@license_version:1.5@@
import threading
from datetime import datetime

import webapp2
from dateutil.relativedelta import relativedelta
from webapp2 import Request, Response

from rogerthat.templates import get_language_from_request
from rogerthat.web_client.models import COOKIE_KEY, WebClientSession, SESSION_EXPIRE_TIME


class CurrentRequest(threading.local):

    def __init__(self):
        self.session = None  # type: WebClientSession

    def set_session(self, session):
        self.session = session

    def get_session(self):
        return self.session


_current_request = CurrentRequest()
del CurrentRequest


def get_current_web_session():
    # type: () -> WebClientSession
    return _current_request.get_session()


class WebRequestHandler(webapp2.RequestHandler):
    session = None  # type: WebClientSession

    def get(self, *args, **kwargs):
        session = handle_web_request(self.request, self.response)
        _current_request.set_session(session)
        self.response.set_cookie(COOKIE_KEY, str(session.id), max_age=SESSION_EXPIRE_TIME, httponly=True)

    def get_language(self):
        session = get_current_web_session()
        return session.language if session else get_language_from_request(self.request)


def handle_web_request(request, response):
    # type: (Request, Response) -> WebClientSession
    cookie = request.cookies.get(COOKIE_KEY)
    now = datetime.now()
    web_session = None
    should_save = False
    if cookie:
        try:
            session_id = long(cookie)
            web_session = WebClientSession.create_key(session_id).get()
            # Only update the session once per day
            if web_session and now > (web_session.last_use_date + relativedelta(days=1)):
                web_session.last_use_date = now
                should_save = True
        except ValueError:
            # Cookie is not an integer/long
            pass
    language = get_language_from_request(request)
    if not web_session:
        web_session = WebClientSession(last_use_date=now, language=language)
        should_save = True
    if web_session.language != language:
        web_session.language = language
        should_save = True
    if should_save:
        web_session.put()
    response.set_cookie(COOKIE_KEY, str(web_session.id), max_age=SESSION_EXPIRE_TIME, httponly=True)
    return web_session
