# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import json
import logging

from mcfw.exceptions import HttpBadRequestException
from mcfw.restapi import GenericRESTRequestHandler, rest
from mcfw.rpc import arguments, returns
from rogerthat.bizz.registration import get_headers_for_consent
from rogerthat.utils import try_or_defer
from solution_server_settings import CampaignMonitorWebhook
from solutions.common.bizz.campaignmonitor import LIST_CALLBACK_PATH, \
    new_list_event


@rest(LIST_CALLBACK_PATH + '/<webhook_id:[^/]+>', 'post', read_only_access=True, authenticated=False)
@returns(dict)
@arguments(webhook_id=unicode)
def api_get_list_webhook_callback(webhook_id):
    """A generic handler for campaignmonitor subscriber list web hooks"""
    if '_type_' in webhook_id:
        list_id, organization_type = [long(v) for v in webhook_id.split('_type_')]
    else:
        list_id = long(webhook_id)
        organization_type = None

    webhook = CampaignMonitorWebhook.get_by_id(list_id)  # type: CampaignMonitorWebhook
    if not webhook:
        raise HttpBadRequestException()

    current_request = GenericRESTRequestHandler.getCurrentRequest()
    list_events = json.loads(current_request.body)
    events_list_id = list_events['ListID']
    events = list_events['Events']

    if organization_type is None:
        if webhook.list_id != events_list_id:
            logging.warn('Invalid list id %s, expected %s', events_list_id, webhook.list_id)
            raise HttpBadRequestException()
    else:
        ol = webhook.get_organization_list(organization_type)
        if not ol:
            logging.warn('Invalid organization_type %s', organization_type)
            raise HttpBadRequestException()
        if ol.list_id != events_list_id:
            logging.warn('Invalid organization list id %s, expected %s', events_list_id, ol.list_id)
            raise HttpBadRequestException()

    headers = get_headers_for_consent(current_request)
    try_or_defer(new_list_event, list_id, events_list_id, events, headers, webhook.consent_type)
    # just to make sure the status code is 200
    return {}
