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

from rogerthat.rpc.service import ServiceApiException


class BrandingValidationException(ServiceApiException):
    def __init__(self, message):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_BRANDING + 0, message)


class BrandingAlreadyExistsException(ServiceApiException):
    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_BRANDING + 1, 'Branding already exists.')


class BrandingInUseException(ServiceApiException):
    def __init__(self, message, **kwargs):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_BRANDING + 2, message, **kwargs)


class BadBrandingZipException(ServiceApiException):
    def __init__(self, reason):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_BRANDING + 3, 'Bad zip file', reason=reason)


class DefaultBrandingRequiredException(ServiceApiException):
    def __init__(self):
        message = 'Cannot remove branding, a default branding is required'
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_BRANDING + 4, message)


class DefaultBrandingNotFoundExcpetion(ServiceApiException):
    def __init__(self, branding_id):
        message = 'Default branding with id %s not found' % branding_id
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_BRANDING + 5, message)
