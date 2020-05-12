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

from rogerthat.rpc.service import ServiceApiException


class FormValidationException(ServiceApiException):

    def __init__(self, msg):
        super(FormValidationException, self).__init__(ServiceApiException.BASE_CODE_FORMS + 1, msg)


class EmptyPropertyException(ServiceApiException):

    def __init__(self, prop, parent):
        msg = u'Property %s is missing or empty from element %s' % (prop, parent)
        super(EmptyPropertyException, self).__init__(ServiceApiException.BASE_CODE_FORMS + 2, msg)


class FormNotFoundException(ServiceApiException):

    def __init__(self, form_id):
        super(FormNotFoundException, self).__init__(ServiceApiException.BASE_CODE_FORMS + 2,
                                                    'Form with id %s not found' % form_id, id=form_id)


class FormInUseException(ServiceApiException):

    def __init__(self, form_id, menu_item_label):
        super(FormInUseException, self).__init__(ServiceApiException.BASE_CODE_FORMS + 3,
                                                 'Form %s is currently in use by menu item "%s" and cannot be deleted.' % (
                                                 form_id, menu_item_label))


class NoPermissionToFormException(ServiceApiException):

    def __init__(self, form_id):
        super(NoPermissionToFormException, self).__init__(ServiceApiException.BASE_CODE_FORMS + 4,
                                                          'You do not have permission to form %d' % form_id)


class SubmitFormException(Exception):
    def __init__(self, message):
        self.message = message
        super(SubmitFormException, self).__init__(message)


class LocalizedSubmitFormException(Exception):
    def __init__(self, reason, **kwargs):
        self.reason = reason
        self.fields = kwargs
        super(LocalizedSubmitFormException, self).__init__('Cannot submit form: %s' % reason)
