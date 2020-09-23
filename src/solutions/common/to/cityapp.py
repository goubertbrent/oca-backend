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

from mcfw.properties import unicode_property, bool_property, typed_property, long_property
from rogerthat.to import TO


class UitdatabankSettingsTO(object):
    enabled = bool_property('1')
    version = unicode_property('2')
    params = typed_property('3', dict)

    @staticmethod
    def from_model(model):
        to = UitdatabankSettingsTO()
        to.enabled = model.enabled
        to.version = model.version
        to.params = model.params
        return to


class UitdatabankCheckTO(TO):
    enabled = bool_property('enabled', default=True)
    errormsg = unicode_property('errormsg', default=None)
    count = long_property('count', default=0)

    @classmethod
    def create(cls, enabled=True, errormsg=None, count=0):
        r = cls()
        r.enabled = enabled
        r.errormsg = unicode(errormsg) if errormsg else None
        r.count = count
        return r
