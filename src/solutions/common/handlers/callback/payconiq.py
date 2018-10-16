# -*- coding: utf-8 -*-
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
# @@license_version:1.4@@
import logging

import webapp2

from rogerthat.utils import try_or_defer
from solution_server_settings import get_solution_server_settings
from solutions.common.bizz.store import verify_payconiq_signature, handle_payconiq_callback
from solutions.common.consts import PAYCONIQ_CERTIFICATES


# See https://dev.payconiq.com/online-payments-dock/#merchant-callback-webhooks-

class PayconiqCallbackHandler(webapp2.RequestHandler):
    def post(self):
        logging.debug(self.request.params)
        webhook_id = self.request.GET.get('webhookId')
        transaction_id = self.request.POST.get('_id')
        status = self.request.POST.get('status')

        signature = self.request.headers.get('X-Security-Signature')
        timestamp = self.request.headers.get('X-Security-Timestamp')
        key_url = self.request.headers.get('X-Security-Key')
        algorithm = self.request.headers.get('X-Security-Algorithm')

        if algorithm != 'SHA256WithRSA':
            logging.debug('Invalid algoritm')
            self.abort(400)
            return
        merchant_id = get_solution_server_settings().payconiq_merchant_id
        public_key = PAYCONIQ_CERTIFICATES[key_url]
        if not verify_payconiq_signature(public_key, merchant_id, timestamp, self.request.body, signature):
            logging.debug('Invalid signature')
            self.abort(400)
        try_or_defer(handle_payconiq_callback, webhook_id, transaction_id, status)
        self.response.set_status(200)
