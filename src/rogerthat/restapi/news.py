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

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.settings import get_server_settings
from rogerthat.to.news import NewsMobileConfigTO


@rest('/mobi/rest/news/config', 'get')
@returns([NewsMobileConfigTO])
@arguments()
def rest_get_news_config_records():
    settings = get_server_settings()
    return [NewsMobileConfigTO.from_string(endpoint) for endpoint in settings.newsServerEndpoints]
