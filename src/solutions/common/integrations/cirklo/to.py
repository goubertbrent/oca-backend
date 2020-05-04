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
from mcfw.properties import typed_property, unicode_property, bool_property, long_property, unicode_list_property
from rogerthat.to import TO


class UpdateVoucherServiceTO(TO):
    providers = unicode_list_property('providers')


class VoucherServiceTO(UpdateVoucherServiceTO):
    name = unicode_property('name')
    service_email = unicode_property('service_email')

    @classmethod
    def from_models(cls, customer, voucher_settings):
        to = cls()
        to.name = customer.name
        to.service_email = customer.service_email
        to.providers = [] if not voucher_settings else voucher_settings.providers
        return to


class VoucherListTO(TO):
    cursor = unicode_property('cursor')
    total = long_property('total')
    more = bool_property('more')
    results = typed_property('results', VoucherServiceTO, True)
