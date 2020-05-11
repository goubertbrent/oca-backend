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

from google.appengine.api import users as gusers

from mcfw.cache import CachedModelMixIn
from mcfw.consts import MISSING
from mcfw.restapi import register_postcall_hook, INJECTED_FUNCTIONS
from mcfw.rpc import serialize_value, get_type_details
from rogerthat.bizz.authentication import get_user_scopes_from_request
from rogerthat.rpc import users
from rogerthat.utils import OFFLOAD_TYPE_WEB, offload
from rogerthat.utils.transactions import on_trans_committed

dummy = lambda: None


def log_restapi_call_result(function, success, kwargs, result_or_error):
    if function.meta['silent']:
        request_data = "****"
    else:
        kwarg_types = function.meta[u"kwarg_types"]
        request_data = dict()
        for arg, value in kwargs.iteritems():
            if arg == 'accept_missing':
                continue
            if value == MISSING:
                continue
            request_data[arg] = serialize_value(value, *get_type_details(kwarg_types[arg], value), skip_missing=True)

    if function.meta['silent_result']:
        result = "****"
    elif isinstance(result_or_error, Exception):
        result = unicode(result_or_error)
    else:
        result = result_or_error
    offload(users.get_current_user() or gusers.get_current_user(), OFFLOAD_TYPE_WEB, request_data,
            result, function.meta['uri'], success)


register_postcall_hook(log_restapi_call_result)
INJECTED_FUNCTIONS.get_current_session = users.get_current_session
INJECTED_FUNCTIONS.get_user_scopes_from_request = get_user_scopes_from_request

del log_restapi_call_result

CachedModelMixIn.on_trans_committed = lambda self, f, *args, **kwargs: on_trans_committed(f, *args, **kwargs)
