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

from createsend.utils import json_to_py
from mcfw.exceptions import HttpBadRequestException
from mcfw.restapi import GenericRESTRequestHandler, rest
from mcfw.rpc import arguments, returns
from rogerthat.bizz.registration import get_headers_for_consent
from rogerthat.utils import try_or_defer
from solution_server_settings import CampaignMonitorWebhook
from solutions.common.bizz.campaignmonitor import LIST_CALLBACK_PATH
from solutions.common.bizz.service import new_list_event


@rest(LIST_CALLBACK_PATH + '/<webhook_id:[^/]+>', 'post', read_only_access=True, authenticated=False)
@returns(dict)
@arguments(webhook_id=(int, long))
def api_list_webhook_callback(webhook_id):
    """A generic handler for campaignmonitor subscriber list web hooks"""
    webhook = CampaignMonitorWebhook.get_by_id(webhook_id)  # type: CampaignMonitorWebhook
    if not webhook:
        raise HttpBadRequestException()
    current_request = GenericRESTRequestHandler.getCurrentRequest()
    list_events = json_to_py(current_request.body)
    if webhook.list_id != list_events.ListID:
        logging.warn('Invalid list id %s, expected %s', list_events.ListID, webhook.list_id)
        raise HttpBadRequestException()
    headers = get_headers_for_consent(current_request)
    try_or_defer(new_list_event, list_events.ListID, list_events.Events, headers, webhook.consent_type)
    # just to make sure the status code is 200
    return {}
