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

from mcfw.exceptions import HttpNotFoundException, HttpConflictException, HttpBadRequestException
from rogerthat.to.payment import ErrorPaymentTO
from rogerthat.translations import localize


class InvalidPaymentProviderException(HttpBadRequestException):
    def __init__(self, payment_provider_id):
        self.payment_provider_id = payment_provider_id
        super(InvalidPaymentProviderException, self).__init__('invalid_payment_provider',
                                                              {'payment_provider_id': payment_provider_id})


class PaymentProviderNotFoundException(HttpNotFoundException):
    def __init__(self, payment_provider_id):
        self.payment_provider_id = payment_provider_id
        super(PaymentProviderNotFoundException, self).__init__('payment_provider_not_found',
                                                               {'payment_provider_id': payment_provider_id})


class PaymentProviderAlreadyExistsException(HttpConflictException):
    def __init__(self, payment_provider_id):
        self.payment_provider_id = payment_provider_id
        super(PaymentProviderAlreadyExistsException, self).__init__('payment_provider_already_exists',
                                                                    {'payment_provider_id': payment_provider_id})


class PaymentProviderNoOauthSettingsException(HttpNotFoundException):
    def __init__(self, payment_provider_id):
        self.payment_provider_id = payment_provider_id
        super(PaymentProviderNoOauthSettingsException, self).__init__('payment_provider_no_oauth_settings',
                                                                      {'payment_provider_id': payment_provider_id})


class InvalidPaymentImageException(HttpBadRequestException):
    def __init__(self, error='invalid_payment_image', data=None):
        super(InvalidPaymentImageException, self).__init__(error, data)


class PaymentException(Exception):

    def __init__(self, error, language, translation_data=None, data=None):
        # type: (unicode, unicode, dict) -> None
        key = 'payments.%s' % error
        self.error = ErrorPaymentTO(error, localize(language, key, **(translation_data or {})), data)
        super(PaymentException, self).__init__(self.error.message)


class UnsupportedEmbeddedAppException(HttpBadRequestException):
    def __init__(self, embedded_app_id):
        self.embedded_app_id = embedded_app_id
        super(UnsupportedEmbeddedAppException, self).__init__('invalid_embedded_app_id',
                                                              {'embedded_app_id': embedded_app_id})
