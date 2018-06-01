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
from google.appengine.ext import ndb

from mcfw.rpc import arguments, returns
from rogerthat.consts import DEBUG
from rogerthat.settings import get_server_settings
from solution_server_settings import get_solution_server_settings, CampaignMonitorWebhook
from solutions.common.models import SolutionServiceConsent


LIST_CALLBACK_PATH = '/unauthenticated/osa/campaignmonitor/callback'


class ListEvents(object):
    """Subscriber list events"""
    SUBSCRIBE = 'Subscribe'
    DEACTIVATE = 'Deactivate'
    UPDATE = 'Update'
    ALL = [SUBSCRIBE, DEACTIVATE, UPDATE]


def get_list_callback_url(webhook_id):
    path = '/'.join([LIST_CALLBACK_PATH, str(webhook_id)])
    return urlparse.urljoin(get_server_settings().baseUrl, path)


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
    consent_keys = [SolutionServiceConsent.create_key(email) for email in to]
    consents = ndb.get_multi(consent_keys)  # type: list[SolutionServiceConsent]
    allowed_to = []
    for email, consent in zip(to, consents):
        if SolutionServiceConsent.consents(consent)[SolutionServiceConsent.TYPE_EMAIL_MARKETING]:
            allowed_to.append(consent.email)
        else:
            logging.info('Not sending email to %s because no consent was given to send marketing emails', email)
    if DEBUG:
        logging.debug('Not sending out smart email %s to %s because DEBUG=True', email_id, allowed_to)
        return
    if not allowed_to:
        return

    cs = Transactional(get_auth_parameters())
    results = cs.smart_email_send(email_id, allowed_to, add_recipients_to_list=add_recipients_to_list)
    rejected = [res.Recipient for res in results if res.Recipient not in allowed_to]
    if rejected:
        logging.error('Sending smart email of %s is rejected for %s', email_id, rejected, _suppress=False)


@returns(List)
@arguments(list_id=unicode)
def get_list(list_id):
    return List(get_auth_parameters(), list_id)


@returns(Subscriber)
@arguments(list_id=unicode, email=unicode)
def get_subscriber(list_id=None, email=None):
    return Subscriber(get_auth_parameters(), list_id, email)


@returns(CampaignMonitorWebhook)
@arguments(list_id=unicode, events=[unicode], consent_type=unicode)
def register_webhook(list_id, events, consent_type):
    """Register or activate a webhook for `events` of `list_id`

    Args:
        list_id (unicode)
        events (list of unicode)
        consent_type (SolutionServiceConsent)

    Returns:
        CampaignMonitorWebhook
    """
    ls = get_list(list_id)
    # Check if a webhook for this list_id already exists
    existing_webhook = CampaignMonitorWebhook.list_by_list_id(list_id).get()
    if existing_webhook:
        return existing_webhook
    datastore_id = CampaignMonitorWebhook.allocate_ids(1)[0]
    callback_url = get_list_callback_url(datastore_id)
    ls.create_webhook(events, callback_url, 'json')  # returns list id, not very useful
    webhook = CampaignMonitorWebhook(id=datastore_id, list_id=list_id, consent_type=consent_type)
    webhook.put()
    return webhook


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
