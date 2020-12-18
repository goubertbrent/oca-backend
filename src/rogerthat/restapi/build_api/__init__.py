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

from __future__ import unicode_literals

from urlparse import urlparse

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.models import AppNameMapping
from rogerthat.restapi.build_api.to import AppDeepLinksTO, AppBuildInfoTO
from rogerthat.settings import get_server_settings
from rogerthat.dal.app import get_app_by_id


@rest('/api/build/apps/<app_id:[^/]+>', 'get')
@returns(AppBuildInfoTO)
@arguments(app_id=unicode)
def rest_get_build_info(app_id):
    server_settings = get_server_settings()
    client_url = urlparse(server_settings.webClientUrl)
    links = [AppDeepLinksTO(host='participatiespaarpot.be',
                            path_prefix='/qr/%s' % app_id,
                            scheme='https')]
    links += [AppDeepLinksTO(host=client_url.hostname,
                             path_prefix='/web/%s/news/id' % app_name_mapping.name,
                             scheme=client_url.scheme) for app_name_mapping in AppNameMapping.list_by_app(app_id)]

    result = AppBuildInfoTO(deep_links=links)
    app = get_app_by_id(app_id)
    if app:
        result.ios_app_id = app.ios_app_id
    return result
