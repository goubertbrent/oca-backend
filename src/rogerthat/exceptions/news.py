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

from rogerthat.models.news import NewsItem
from rogerthat.rpc.service import ServiceApiException


class NewsNotFoundException(ServiceApiException):
    def __init__(self, news_id):
        message = u'News with id %d not found' % news_id
        super(NewsNotFoundException, self).__init__(self.BASE_CODE_NEWS + 1, message)


class CannotUnstickNewsException(ServiceApiException):
    def __init__(self):
        message = u'Cannot unstick news'
        super(CannotUnstickNewsException, self).__init__(self.BASE_CODE_NEWS + 2, message)


class TooManyNewsButtonsException(ServiceApiException):
    def __init__(self):
        message = u'Too many news buttons. Maximum is 3 buttons, when flags are set to 0.'
        super(TooManyNewsButtonsException, self).__init__(self.BASE_CODE_NEWS + 3, message)


class CannotChangePropertyException(ServiceApiException):
    def __init__(self, property_name):
        message = u'Property \'%s\' cannot be changed after publishing the news item.' % property_name
        super(CannotChangePropertyException, self).__init__(self.BASE_CODE_NEWS + 4, message)


class MissingNewsArgumentException(ServiceApiException):
    def __init__(self, param):
        message = u'Parameter %s is missing' % param
        super(MissingNewsArgumentException, self).__init__(self.BASE_CODE_NEWS + 5, message)


class InvalidNewsTypeException(ServiceApiException):
    def __init__(self, news_type):
        message = u'News type %s is not valid. Allowed types are %s' % (news_type, u', '.join(NewsItem.TYPES))
        super(InvalidNewsTypeException, self).__init__(self.BASE_CODE_NEWS + 6, message)


class NoPermissionToNewsException(ServiceApiException):
    def __init__(self, requesting_user):
        message = u'You (%s) don\'t have permission to this news item.' % requesting_user
        super(NoPermissionToNewsException, self).__init__(self.BASE_CODE_NEWS + 7, message)


class ValueTooLongException(ServiceApiException):
    def __init__(self, prop, max_length):
        message = 'The value of the property \'%s\' is too long. Only %d characters are allowed.' % (prop, max_length)
        super(ValueTooLongException, self).__init__(self.BASE_CODE_NEWS + 8, message)


class DemoServiceException(ServiceApiException):
    def __init__(self, app_id):
        message = 'A demo service may only publish news in demo apps. %s is not a demo app.' % app_id
        super(DemoServiceException, self).__init__(self.BASE_CODE_NEWS + 9, message)


class InvalidScheduledTimestamp(ServiceApiException):
    def __init__(self):
        message = u'Scheduled timestamp must be in the future'
        super(InvalidScheduledTimestamp, self).__init__(self.BASE_CODE_NEWS + 11, message)


class EmptyActionButtonCaption(ServiceApiException):
    def __init__(self):
        message = u'Action button caption is empty'
        super(EmptyActionButtonCaption, self).__init__(self.BASE_CODE_NEWS + 13, message)


class InvalidActionButtonRoles(ServiceApiException):
    def __init__(self):
        message = u'This news item is missing action button roles'
        super(InvalidActionButtonRoles, self).__init__(self.BASE_CODE_NEWS + 14, message)


class InvalidActionButtonFlowParamsException(ServiceApiException):
    def __init__(self, button):
        message = u'This flow_params of action button %s must be parseable as json' % button
        super(InvalidActionButtonFlowParamsException, self).__init__(self.BASE_CODE_NEWS + 15, message)
