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

import logging

from google.appengine.ext import deferred
import webapp2

from rogerthat.templates import get_languages_from_request
from shop.models import StripePayment
from solution_server_settings import get_solution_server_settings
from solutions.common.bizz.store import stripe_order_completed
from solutions.common.handlers import JINJA_ENVIRONMENT
import stripe


class StripeHandler(webapp2.RequestHandler):

    def get(self):
        session_id = self.request.get('session_id')
        try:
            payment = StripePayment.create_key(session_id).get()
        except:
            payment = None

        if not payment:
            logging.debug('payment with session_id:%s not found', session_id)
            self.redirect("/ourcityapp")
            return

        language = get_languages_from_request(self.request)[0]
        params = {
            'CHECKOUT_SESSION_ID': session_id,
            'language': language
        }

        jinja_template = JINJA_ENVIRONMENT.get_template('pages/stripe_redirect.html')
        self.response.out.write(jinja_template.render(params))


class StripeSuccessHandler(webapp2.RequestHandler):

    def get(self):
        language = get_languages_from_request(self.request)[0]
        jinja_template = JINJA_ENVIRONMENT.get_template('pages/stripe_success.html')
        self.response.out.write(jinja_template.render({'language': language}))


class StripeCancelHandler(webapp2.RequestHandler):

    def get(self):
        language = get_languages_from_request(self.request)[0]
        jinja_template = JINJA_ENVIRONMENT.get_template('pages/stripe_cancel.html')
        self.response.out.write(jinja_template.render({'language': language}))


class StripeWebhookHandler(webapp2.RequestHandler):

    def post(self):
        payload = self.request.body
        sig_header = self.request.headers.get('Stripe-Signature')

        solution_server_settings = get_solution_server_settings()
        webhook_secret = solution_server_settings.stripe_webhook_secret

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            logging.debug('Invalid payload', exc_info=True)
            self.abort(400)
            return
        except stripe.error.SignatureVerificationError:
            logging.debug('Invalid signature', exc_info=True)
            self.abort(400)
            return

        logging.debug(event)
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            deferred.defer(stripe_order_completed, session['id'])


