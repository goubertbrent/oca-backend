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

import httplib
import json

from google.appengine.api import urlfetch


class HttpException(Exception):
    http_code = 0

    def __init__(self, error=None, data=None, **kwargs):
        self.data = data or {}
        if not error and self.http_code in httplib.responses:
            error = httplib.responses[self.http_code]
        self.error = error
        super(HttpException, self).__init__(self, error, **kwargs)

    @classmethod
    def from_urlfetchresult(cls, urlfetch_result):
        # type: (urlfetch._URLFetchResult) -> HttpException
        err_cls = MAPPING.get(urlfetch_result.status_code)
        error = None
        data = None
        try:
            content = json.loads(urlfetch_result.content)
            if 'error' in content:
                error = content['error']
            if 'data' in content:
                data = content['data']
        except:
            pass
        if not err_cls:
            err = HttpException(error, data)
            err.http_code = urlfetch_result.status_code
        else:
            err = err_cls(error, data)
        return err


class HttpBadRequestException(HttpException):
    http_code = httplib.BAD_REQUEST

    def __init__(self, *args, **kwargs):
        super(HttpBadRequestException, self).__init__(*args, **kwargs)


class HttpUnAuthorizedException(HttpException):
    http_code = httplib.UNAUTHORIZED

    def __init__(self, *args, **kwargs):
        super(HttpUnAuthorizedException, self).__init__(*args, **kwargs)


class HttpForbiddenException(HttpException):
    http_code = httplib.FORBIDDEN

    def __init__(self, *args, **kwargs):
        super(HttpForbiddenException, self).__init__(*args, **kwargs)


class HttpNotFoundException(HttpException):
    http_code = httplib.NOT_FOUND

    def __init__(self, *args, **kwargs):
        super(HttpNotFoundException, self).__init__(*args, **kwargs)


class HttpConflictException(HttpException):
    http_code = httplib.CONFLICT

    def __init__(self, *args, **kwargs):
        super(HttpConflictException, self).__init__(*args, **kwargs)


class HttpUnprocessableEntityException(HttpException):
    http_code = httplib.UNPROCESSABLE_ENTITY

    def __init__(self, *args, **kwargs):
        super(HttpUnprocessableEntityException, self).__init__(*args, **kwargs)


class HttpInternalServerErrorException(HttpException):
    http_code = httplib.INTERNAL_SERVER_ERROR

    def __init__(self, *args, **kwargs):
        super(HttpInternalServerErrorException, self).__init__(*args, **kwargs)


class HttpBadGatewayException(HttpException):
    http_code = httplib.BAD_GATEWAY

    def __init__(self, *args, **kwargs):
        super(HttpBadGatewayException, self).__init__(*args, **kwargs)


MAPPING = {
    400: HttpBadRequestException,
    401: HttpUnAuthorizedException,
    403: HttpForbiddenException,
    404: HttpNotFoundException,
    409: HttpConflictException,
    422: HttpUnprocessableEntityException,
    500: HttpInternalServerErrorException,
    502: HttpBadGatewayException,
}
