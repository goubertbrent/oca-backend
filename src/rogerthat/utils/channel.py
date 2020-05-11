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

import json
import logging
import os

from google.appengine.ext import db

from rogerthat.consts import MC_DASHBOARD
from rogerthat.models import App
from rogerthat.rpc import users
from rogerthat.utils import try_or_defer, offload, OFFLOAD_TYPE_WEB_CHANNEL, now
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.transactions import on_trans_committed


def get_data(type_, **kwargs):
    if isinstance(type_, list):
        data = type_
    else:
        kwargs[u'type'] = type_
        data = kwargs

    return data


def get_data_as_json(type_, service_identity=None, **kwargs):
    data = {
        'data': json.dumps(get_data(type_, **kwargs)),
        'service_identity': service_identity,
        'timestamp': now()
    }

    return json.dumps(data)


def send_message_to_session(service_user, session, type_, **kwargs):
    data = get_data_as_json(type_, **kwargs)
    offload(service_user, OFFLOAD_TYPE_WEB_CHANNEL, data, None, type_)

    if db.is_in_transaction():
        on_trans_committed(try_or_defer, _send_message, service_user, data, session)
    else:
        try_or_defer(_send_message, service_user, data, session)


def send_message(user, type_, skip_dashboard_user=True, service_identity=None, silent=False, **kwargs):
    if u"SERVER_SOFTWARE" in os.environ:
        data = get_data_as_json(type_, service_identity, **kwargs)

        targets = []
        for u in (user if isinstance(user, (set, list, tuple)) else [user]):
            if skip_dashboard_user and u == MC_DASHBOARD:
                continue

            targets.append(u if isinstance(user, users.User) else users.User(u))

        for user in targets:
            if ':' in user.email() and get_app_id_from_app_user(user) != App.APP_ID_ROGERTHAT:
                logging.info('Not sending channel message for user %s because web only supports \'rogerthat\'',
                             user.email())
                return
            if not silent:
                offload(user, OFFLOAD_TYPE_WEB_CHANNEL, data, None, type_)
            if db.is_in_transaction():
                on_trans_committed(try_or_defer, _send_message, user, data)
            else:
                try_or_defer(_send_message, user, data)
        return True


def _send_message(user, data, session=None):
    from rogerthat.bizz import channel
    if session:
        user_or_session_id = unicode(session.key())
    else:
        user_or_session_id = user.email()
    channel.send_message(user_or_session_id, data)


def broadcast_via_iframe_result(type_, **kwargs):
    return """<html><body><script language="javascript" type="text/javascript">
    var obj = window.top.window.mctracker ? window.top.window.mctracker : window.top.window.sln; obj.broadcast(%s);
</script></body></html>""" % json.dumps(get_data(type_, **kwargs))
