# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley NV
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
from google.appengine.api import urlfetch

from rogerthat.bizz.maps.reports import _do_request
from rogerthat.dal.profile import get_service_profile
from rogerthat.rpc import users


def list_incidents(service_user, params):
    # type: (users.User, dict) -> dict
    service_profile = get_service_profile(service_user)
    return _do_request('/incidents', params=params, language=service_profile.defaultLanguage,
                       authorization=service_profile.sik)


def get_incident(service_user, incident_id):
    # type: (users.User, str) -> dict
    service_profile = get_service_profile(service_user)
    return _do_request('/incidents/%s' % incident_id, language=service_profile.defaultLanguage,
                       authorization=service_profile.sik)


def update_incident(service_user, incident_id, data):
    # type: (users.User, str, dict) -> dict
    service_profile = get_service_profile(service_user)
    return _do_request('/incidents/%s' % incident_id, urlfetch.PUT, data, language=service_profile.defaultLanguage,
                       authorization=service_profile.sik)
