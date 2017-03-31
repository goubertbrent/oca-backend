# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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
# @@license_version:1.2@@

from mcfw.properties import unicode_property

class LocationTO(object):
    identity = unicode_property('1')
    name = unicode_property('2')
    phone_number = unicode_property('3')
    address = unicode_property('4')
    location_url = unicode_property('5')

    @classmethod
    def create(cls, identity, obj):
        to = cls()
        to.identity = identity
        to.name = obj.name
        to.phone_number = obj.phone_number
        to.address = obj.address
        if obj.location:
            to.location_url = u"https://www.google.com/maps/preview?daddr=%s,%s" % (obj.location.lat, obj.location.lon)
        else:
            to.location_url = None
        return to
