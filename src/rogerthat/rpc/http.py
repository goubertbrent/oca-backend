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

import base64
import json
import logging
import threading
import time

import webapp2
from google.appengine.api import memcache
from google.appengine.ext import db

from mcfw.properties import azzert
from rogerthat.consts import MAX_RPC_SIZE, DEBUG
from rogerthat.dal.rpc_call import get_limited_backlog, get_filtered_backlog
from rogerthat.rpc import users
from rogerthat.rpc.models import Mobile, OutStandingFirebaseKick
from rogerthat.rpc.rpc import API_VERSION, call, cresult, API_DIRECT_PATH_KEY, ack_all, wait_for_rpcs, \
    parse_and_validate_request, CALL_ID, ERROR, STATUS, CALL_TIMESTAMP, STATUS_FAIL, APPENGINE_APP_ID, \
    rpc_items
from rogerthat.rpc.users import authenticate_user
from rogerthat.settings import get_server_settings
from rogerthat.utils import now, offload, OFFLOAD_TYPE_APP


class RequestTracker(threading.local):
    def __init__(self):
        self.current_request = None


_current_request_tracker = RequestTracker()
del RequestTracker


def get_current_request():
    return _current_request_tracker.current_request


class JSONRPCRequestHandler(webapp2.RequestHandler):
    INSTANT = False

    def post(self):
        if not self.set_user():
            self.response.set_status(500)
            return
        try:
            _current_request_tracker.current_request = self.request
            body = self.request.body
            json_result = process(body, instant=self.INSTANT)

            self.response.headers['Content-Type'] = 'application/json-rpc'
            self.response.out.write(json_result)
        finally:
            users.clear_user()

    def set_user(self):
        user = self.request.headers.get("X-MCTracker-User", None)
        password = self.request.headers.get("X-MCTracker-Pass", None)
        if not user or not password:
            return False
        return users.set_json_rpc_user(base64.decodestring(user), base64.decodestring(password))


class InstantJSONRPCRequestHandler(JSONRPCRequestHandler):
    INSTANT = True


class UserAuthenticationHandler(webapp2.RequestHandler):
    def post(self):
        user = self.request.headers.get('X-MCTracker-User')
        password = self.request.headers.get('X-MCTracker-Pass')
        if not authenticate_user(base64.decodestring(user), base64.decodestring(password)):
            self.abort(401)


def process(body, instant=False):
    try:
        request = json.loads(body)
    except:
        logging.warn(body)
        raise
    mobile = users.get_current_mobile()
    jid = mobile.account

    memcache_rpc = memcache.Client().set_multi_async(
        {"last_user_heart_beat_%s" % users.get_current_user().email(): now()})

    logging.info("Incoming HTTP call from %s", jid)

    azzert(request[API_VERSION] == 1)
    responses = []
    acks = []
    calls = []

    starttime = now()

    timeToStartFlushing = lambda: now() - starttime > 15

    sizes = []

    def processResult(r):
        users.set_backlog_item(r)
        try:
            ack = cresult(r)
            acks.append(ack)
            sizes.append(len(ack))
        finally:
            users.set_backlog_item(None)

    def processCall(c):
        users.set_backlog_item(c)
        try:
            if mobile.is_phone_unregistered:
                # Do not process calls coming from an unregistered app.
                api_version, callid, _, _ = parse_and_validate_request(c)
                timestamp = c[CALL_TIMESTAMP] if CALL_TIMESTAMP in c else now()
                result = {
                    CALL_ID: callid,
                    API_VERSION: api_version,
                    ERROR: "Unknown function call!",
                    STATUS: STATUS_FAIL,
                    CALL_TIMESTAMP: timestamp}
            else:
                result = call(c, instant=instant)
                if not result:
                    return
                _, result = result
            responses.append(result)
            sizes.append(len(json.dumps(result)))
        finally:
            users.set_backlog_item(None)

    def stream():
        if not instant:
            ack_all(request.get(u"a", []))
            for r in request.get(u"r", []):
                yield processResult, r
                if timeToStartFlushing() or sum(sizes) > MAX_RPC_SIZE:
                    return
        for c in request.get(u"c", []):
            yield processCall, c
            if timeToStartFlushing() or sum(sizes) > MAX_RPC_SIZE:
                return

    for f, a in stream():
        f(a)

    if not DEBUG and not instant:
        wait_for_rpcs()

    if mobile.type in Mobile.ANDROID_TYPES and mobile.pushId and not instant:
        rpc_items.append(db.delete_async(OutStandingFirebaseKick.createKey(mobile.pushId)), None)

    more = False
    if sum(sizes) > MAX_RPC_SIZE:
        more = True
    elif not instant:
        count = 0
        deferred_kicks = []

        while True:
            if mobile.is_phone_unregistered:
                memcache_key = "unregistered" + str(mobile.key())
                if memcache.get(memcache_key):  # @UndefinedVariable
                    logging.debug("send empty result to give the phone the chance to finish unregistering")
                    break
                logging.debug("%s (user: %s. status: %s) should unregister itself. "
                              "Close the communication channel via only allowing the Unregister Call",
                              mobile.account, mobile.user, mobile.status)
                qry = get_filtered_backlog(mobile, "com.mobicage.capi.system.unregisterMobile")
            else:
                # Stream the backlog as normal
                qry = get_limited_backlog(mobile, 21)
            for b in qry:
                count += 1
                calls.append(json.loads(b.call))
                sizes.append(len(b.call))
                if b.deferredKick:
                    deferred_kicks.append(b.key().name())
                if sum(sizes) > MAX_RPC_SIZE:
                    more = True
                    break
            if mobile.is_phone_unregistered:
                if not calls:
                    logging.debug("No unregister calls found in the backlog, re-add it.")
                    from rogerthat.bizz.system import unregister_mobile
                    unregister_mobile(users.get_current_user(), mobile)
                    time.sleep(2)  # Make sure when the query runs again, we will get results
                else:
                    memcache.set(memcache_key, "call sent", 60)  # @UndefinedVariable
                    break
            else:
                break

        if count == 21:
            calls.pop()
            more = True
        memcache_stuff = {}
        for c in calls:
            call_id = c["ci"]
            if call_id in deferred_kicks:
                memcache_stuff["capi_sent_to_phone:%s" % call_id] = True
        if memcache_stuff:
            memcache.set_multi(memcache_stuff, 10)  # @UndefinedVariable

    result = {API_VERSION: 1}
    endpoint = u'/json-rpc/instant' if instant else u'/json-rpc'
    if DEBUG:
        result[API_DIRECT_PATH_KEY] = "%s%s" % (get_server_settings().baseUrl, endpoint)
    else:
        result[API_DIRECT_PATH_KEY] = u"https://%s.appspot.com%s" % (APPENGINE_APP_ID, endpoint)
    if responses:
        result[u"r"] = responses
    if acks:
        result[u"a"] = acks
    if calls:
        result[u"c"] = calls
    result[u"more"] = more
    result[u"t"] = now()

    memcache_rpc.get_result()

    offload(users.get_current_user(), OFFLOAD_TYPE_APP, request, result)
    return json.dumps(result)
