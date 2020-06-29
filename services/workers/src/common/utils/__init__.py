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


import logging
import time

from google.appengine.ext.deferred.deferred import PermanentTaskFailure

from common.mcfw.properties import azzert


def now():
    return int(time.time())

def foreach(func, iterable, *args, **kwargs):
    for item in iterable:
        func(item, *args, **kwargs)


def runeach(iterable):
    foreach(lambda f: f(), iterable)
    
    
def get_current_queue():
    return _get_request_header('X-Appengine-Queuename')


def get_current_task_name():
    return _get_request_header('X-Appengine-TaskName')


def _get_request_header(header_name):
    try:
        import webapp2
        request = webapp2.get_request()
        if request:
            return request.headers.get(header_name, None)
    except:
        logging.warn('Failed to get header %s' % header_name, exc_info=1)
        

class BusinessException(PermanentTaskFailure):
    pass


def bizz_check(condition, error_message='', error_class=None):
    if not condition:
        if error_class is None:
            error_class = BusinessException
        else:
            azzert(issubclass(error_class, BusinessException))
        raise error_class(error_message)