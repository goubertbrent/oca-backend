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
from typing import List

from mcfw.properties import unicode_property, long_property, bool_property, typed_property, unicode_list_property
from rogerthat.to import TO


class AutoConnectedServiceTO(TO):
    service_email = unicode_property('service_email')
    removable = bool_property('removable')


class BaseCommunityTO(TO):
    auto_connected_services = typed_property('auto_connected_services', AutoConnectedServiceTO,
                                             True)  # type: List[AutoConnectedServiceTO]
    country = unicode_property('country')
    create_date = unicode_property('create_date')
    default_app = unicode_property('default_app')
    demo = bool_property('demo')
    embedded_apps = unicode_list_property('embedded_apps')
    features = unicode_list_property('features')
    name = unicode_property('name')
    main_service = unicode_property('main_service')
    signup_enabled = bool_property('signup_enabled')


class CommunityTO(BaseCommunityTO):
    id = long_property('id')
