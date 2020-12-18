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

from mcfw.properties import unicode_property, typed_property
from rogerthat.to import TO


class AppDeepLinksTO(TO):
    host = unicode_property('host')
    path_prefix = unicode_property('path_prefix')
    scheme = unicode_property('scheme')

    def __init__(self, host=None, path_prefix=None, scheme=None):
        self.host = host
        self.path_prefix = path_prefix
        self.scheme = scheme


class AppBuildInfoTO(TO):
    deep_links = typed_property('deep_links', AppDeepLinksTO, True)  # type: List[AppDeepLinksTO]
    ios_app_id = unicode_property('ios_app_id', default=None)
