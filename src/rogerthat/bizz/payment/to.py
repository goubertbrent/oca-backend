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

from mcfw.properties import bool_property, unicode_list_property, unicode_property, typed_property


class BankDataTO(object):
    bankCode = unicode_property('bankCode')
    name = unicode_property('name')
    bic = unicode_property('bic')


class OpenIbanResultTO(object):
    valid = bool_property('valid')
    messages = unicode_list_property('message')
    iban = unicode_property('iban')
    bankData = typed_property('bankData', BankDataTO)  # type: BankDataTO
    checkResults = typed_property('checkResults', dict)
