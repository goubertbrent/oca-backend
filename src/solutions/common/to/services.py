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

from mcfw.properties import typed_property, long_property, unicode_property


class ServiceListTO(object):
    service_email = unicode_property('0')
    name = unicode_property('1')
    customer_id = long_property('4')

    def __init__(self, service_email=None, name=None, customer_id=None):
        self.service_email = service_email
        self.name = name
        self.customer_id = customer_id


class ServicesTO(object):
    services = typed_property('1', ServiceListTO, True)
    cursor = unicode_property('3')

    def __init__(self, services=None, cursor=None):
        self.services = services
        self.cursor = cursor
