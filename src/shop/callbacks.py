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

import inspect
import json
import logging

import webapp2

from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import try_or_defer
from mcfw.rpc import parse_complex_value
from shop.business.prospect import add_new_prospect_from_discovery
from solution_server_settings import get_solution_server_settings

SUSPECT_TAG = 'suspect'


def process_callback(request, sik):
    response = dict()
    method = request["method"]
    id_ = request["id"]
    response["id"] = id_
    logging.info("Incoming Rogerthat callback:\n%s", request)
    m = getattr(inspect.getmodule(test_test), method.replace(".", "_"), None)
    if not m:
        response["result"] = None
        response["error"] = None
    else:
        try:
            params = dict()
            for p, v in request["params"].iteritems():
                params[str(p)] = v
            response["result"] = m(sik, id_, **params)
            response["error"] = None
        except Exception, e:
            response["result"] = None
            response["error"] = str(e)
            logging.exception("Incoming %s Rogerthat callback failed.", method)
    logging.debug("Response for incoming %s Rogerthat callback:\n%s", method, response)
    return response


class ProspectDiscoverCallbackHandler(webapp2.RequestHandler):
    def post(self):
        sik = self.request.headers.get("X-Nuntiuz-Service-Key", None)
        solution_server_settings = get_solution_server_settings()
        if not sik or sik != solution_server_settings.shop_new_prospect_sik:
            logging.error("unauthorized access in callback handler: %s", sik)
            self.abort(401)
            return
        request = json.loads(self.request.body)
        # PERFORM CALL
        response = process_callback(request, sik)
        # WIRE RESULT
        self.response.headers['Content-Type'] = 'application/json-rpc'
        json.dump(response, self.response.out)


def test_test(sik, id_, value, **kwargs):
    return value


def messaging_flow_member_result(sik, id_, steps, user_details, tag, **kwargs):
    if tag == SUSPECT_TAG:
        try_or_defer(add_new_prospect_from_discovery, parse_complex_value(UserDetailsTO, user_details, True)[0], steps)
    return None
