# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

import logging

from rogerthat.bizz.session import switch_to_service_identity, create_session
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.utils.cookie import set_cookie
from rogerthat.utils.service import create_service_identity_user
from shop.dal import get_customer
from shop.exceptions import CustomerNotFoundException
from shop.models import Customer
from solutions.common.dal import get_solution_settings
import webapp2


class LoginAsServiceHandler(webapp2.RequestHandler):

    def get(self):
        customer_id = int(self.request.get("customer_id"))
        try:
            customer = Customer.get_by_id(customer_id)
        except CustomerNotFoundException:
            self.abort(404)

        current_user = users.get_current_user()
        current_customer = get_customer(current_user)
        sln_settings = get_solution_settings(current_user)
        if not sln_settings.can_edit_services(current_customer) or not current_customer.can_edit_service():
            logging.warn('Service or user %s is trying to login to the dashboard of %s',
                         current_user.email(), customer.name)
            self.abort(401)

        service_identity_user = create_service_identity_user(users.User(customer.service_email))
        current_session = users.get_current_session()
        new_secret, new_session = create_session(service_identity_user, ignore_expiration=True)
        set_cookie(self.response, get_server_settings().cookieSessionName, new_secret)
        new_session = switch_to_service_identity(new_session, service_identity_user,
                                                 read_only=False,
                                                 shop=current_session.shop,
                                                 layout_only=True)
        new_session.parent_session_secret = current_session.secret
        new_session.put()
        self.redirect("/")
