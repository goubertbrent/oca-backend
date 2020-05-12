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

# For unit tests: we set the log level to ERROR in order not to pollute
# unit test output


import uuid

from google.appengine.api import users as gusers


def register_tst_mobile(email):
    from rogerthat.rpc.models import Mobile
    from rogerthat.rpc import users
    from rogerthat.dal.profile import get_user_profile
    from rogerthat.models.properties.profiles import MobileDetails
    account = unicode(uuid.uuid4()) + u"@mc-tracker.com"
    m = Mobile(key_name=account)
    m.id = unicode(uuid.uuid4())
    m.user = users.User(email)
    m.account = account
    m.description = email
    m.status = Mobile.STATUS_NEW | Mobile.STATUS_ACCOUNT_CREATED | Mobile.STATUS_REGISTERED
    m.type = Mobile.TYPE_ANDROID_HTTP
    m.put()
    p = get_user_profile(m.user)
    if not p.mobiles:
        p.mobiles = MobileDetails()
        p.mobiles.addNew(account, Mobile.TYPE_ANDROID_HTTP, None, u"rogerthat")
    p.put()
    return m


def create_call(apiversion, function, arguments):
    callid = unicode(uuid.uuid4())
    c = dict()
    c["av"] = apiversion
    c["f"] = function
    c["ci"] = callid
    c["a"] = arguments
    return callid, c


def assert_result(result, callId, success, fnCheckResult=None):
    assert result['ci'] == callId
    assert result['s'] == ("success" if success else "fail")
    if success and fnCheckResult != None:
        assert fnCheckResult(result['r'])
    return result['r']


class set_current_user(object):
    def __init__(self, user, is_mfr=False, skip_create_session=False, set_google_user=True):
        from rogerthat.rpc import users
        self.previous_current_user = users.get_current_user()
        self.previous_current_session = users.get_current_session()
        self.previous_current_guser = gusers.get_current_user()
        user.is_mfr = is_mfr
        self._set_user(user, skip_create_session, set_google_user)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        from rogerthat.rpc import users
        users.get_current_user = lambda: self.previous_current_user
        self._set_user(self.previous_current_user, self.previous_current_session is None, self.previous_current_guser)

    def _set_user(self, user, skip_create_session=False, set_google_user=True):
        from rogerthat.bizz.session import create_session
        from rogerthat.rpc import users
        gusers.get_current_user = lambda: user if set_google_user else None
        users.get_current_user = lambda: user
        if user:
            users.get_current_app_id = lambda: user.email().split(':')[1] if ':' in user.email() else "rogerthat"
        else:
            users.get_current_app_id = lambda: None
        session = None if skip_create_session else create_session(user)[1]
        users.get_current_session = lambda: session


def set_current_mobile(mobile):
    from rogerthat.rpc import users
    users.get_current_mobile = lambda: mobile
    set_current_user(mobile.user)
