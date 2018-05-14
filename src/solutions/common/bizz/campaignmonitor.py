# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

import logging
import urlparse

from createsend import BadRequest, List, Transactional, Subscriber

from mcfw.rpc import arguments, returns
from rogerthat.consts import DEBUG
from rogerthat.settings import get_server_settings

from solution_server_settings import get_solution_server_settings


LIST_CALLBACK_PATH = '/unauthenticated/osa/campaignmonitor/callback'


class ListEvents(object):
    """Subscriber list events"""
    SUBSCRIBE = 'Subscribe'
    DEACTIVATE = 'Deactivate'
    UPDATE = 'Update'
    ALL = [SUBSCRIBE, DEACTIVATE, UPDATE]


def get_list_callback_url():
    if DEBUG:
        # FIXME: this is a public ip to test the hooks, can be removed later
        return urlparse.urljoin('http://151fdc2e.ngrok.io', LIST_CALLBACK_PATH)
    return urlparse.urljoin(get_server_settings().baseUrl, LIST_CALLBACK_PATH)


def get_api_key():
    return get_solution_server_settings().createsend_api_key


def get_auth_parameters():
    return {
        'api_key': get_api_key()
    }

@returns()
@arguments(email_id=unicode, to=[unicode], add_recipients_to_list=bool)
def send_smart_email(email_id, to, add_recipients_to_list=True):
    """Send a smart email"""
    if DEBUG:
        logging.debug('Not sending out smart email %s to %s because DEBUG=True', email_id, to)
        return

    try:
        cs = Transactional(get_auth_parameters())
        results = cs.smart_email_send(email_id, to, add_recipients_to_list=add_recipients_to_list)
        rejected = [res.Recipient for res in results if res.Recipient not in to]
        if rejected:
            raise Exception('Sending smart email of %s is rejected for %s' % (email_id, rejected))
    except:
        logging.error('Cannot send smart email to %s', to, exc_info=True, _suppress=False)


@returns(List)
@arguments(list_id=unicode)
def get_list(list_id):
    return List(get_auth_parameters(), list_id)


@returns(Subscriber)
@arguments(list_id=unicode, email=unicode)
def get_subscriber(list_id=None, email=None):
    return Subscriber(get_auth_parameters(), list_id, email)


@returns(unicode)
@arguments(list_id=unicode, events=[unicode])
def register_webhook(list_id, events):
    """Register or activate a webhook for `events` of `list_id`

    Args:
        list_id (unicode)
        events (list of unicode)

    Returns:
        unicode: webhook id
    """
    ls = get_list(list_id)
    callback_url = get_list_callback_url()
    # first get all hooks and check if the events and callback url already exist
    # if so, activate the hook if not activated, and return its id
    hooks = ls.webhooks()
    for hook in hooks:
        if hook.Url == callback_url and set(hook.Events).issubset(events):
            if not hook.Status == 'Active':
                ls.activate_webhook(hook.WebhookID)
            return hook.WebhookID
    return ls.create_webhook(events, callback_url, 'json')


@returns()
@arguments(list_id=unicode, email=unicode, name=unicode, custom_fields=dict)
def subscribe(list_id, email, name=None, custom_fields=None):
    if not name:
        name = email
    get_subscriber(list_id, email).add(list_id, email, name, custom_fields, resubscribe=True)


@returns()
@arguments(list_id=unicode, email=unicode)
def unsubscribe(list_id, email):
    try:
        get_subscriber(list_id, email).unsubscribe()
    except BadRequest as exception:
        # pass if it's already unsubscribed (203)
        if exception.data.Code != 203:
            raise
