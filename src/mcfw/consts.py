# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

class MissingClass(object):

    def __reduce__(self):
        # See pickle documentation:
        #
        # If a string is returned, the string should be interpreted as the name of a global variable.
        # It should be the objects local name relative to its module; the pickle module searches the module
        # namespace to determine the objects module. This behaviour is typically useful for singletons.
        return 'MISSING'

    def default(self, value, value_if_missing):
        return value_if_missing if value is self else value


MISSING = MissingClass()
del MissingClass

AUTHENTICATED = "authenticated"
NOT_AUTHENTICATED = "non_authenticated"

REST_TYPE_NORMAL = u"normal"
REST_TYPE_TO = u"to"
