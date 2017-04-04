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
# @@license_version:1.3@@

import logging

from google.appengine.api import users as gusers
from mcfw.properties import azzert
from mcfw.rpc import arguments
from mcfw.rpc import returns
from rogerthat.utils import try_or_defer
from rogerthat.utils.transactions import run_in_xg_transaction
from solution_server_settings import get_solution_server_settings
from shop.bizz import user_has_permissions_to_team
from shop.exceptions import NoPermissionException
from shop.models import Customer, CreditCard
import stripe


@returns(unicode)
@arguments(customer_id_or_service_email=(int, long, unicode), stripe_token=unicode, stripe_token_created=(int, long),
           contact_id=(int, long))
def link_stripe_to_customer(customer_id_or_service_email, stripe_token, stripe_token_created, contact_id):
    solution_server_settings = get_solution_server_settings()
    stripe.api_key = solution_server_settings.stripe_secret_key
    if isinstance(customer_id_or_service_email, unicode):
        customer = Customer.get_by_service_email(customer_id_or_service_email)
    else:
        customer = Customer.get_by_id(customer_id_or_service_email)

    # Resellers and their customers should not be able to do this
    google_user = gusers.get_current_user()
    if not customer.team.legal_entity.is_mobicage:
        logging.error("user %s tried to access function 'link_stripe_to_customer'", google_user.email())
        raise NoPermissionException()
    if google_user:
        azzert(user_has_permissions_to_team(google_user, customer.team_id))

    if customer.stripe_id:
        stripe_customer = stripe.Customer.retrieve(customer.stripe_id)
        card = stripe_customer.cards.create(card=stripe_token)
        stripe_customer.default_card = card.id
        stripe_customer.save()
    else:
        stripe_customer = stripe.Customer.create(
            card=stripe_token,
            description=u"%s %s -- %s, %s, %s, %s, %s, %s" % (
                customer.id, customer.vat, customer.name, customer.address1, customer.address2, customer.zip_code,
                customer.city, customer.country)
        )
        card = stripe_customer.cards.data[0]
    try_or_defer(store_stripe_link_to_datastore, customer.key(), stripe_customer.id, card.id, stripe_token_created,
                 contact_id)


def store_stripe_link_to_datastore(customer_key, stripe_customer_id, stripe_card_id, stripe_token_created, contact_id):
    def trans():
        customer = Customer.get(customer_key)

        if customer.stripe_id:
            if customer.stripe_credit_card_id:
                old_cc = CreditCard.get_by_key_name(customer.stripe_credit_card_id, parent=customer)
                old_cc.deleted = True
                old_cc.put()
        else:
            customer.stripe_id = stripe_customer_id

        cc = CreditCard(key_name=stripe_card_id, parent=customer)
        cc.creation_time = stripe_token_created
        cc.contact_id = contact_id
        cc.put()

        customer.stripe_id_created = stripe_token_created
        customer.stripe_credit_card_id = stripe_card_id
        customer.put()

    run_in_xg_transaction(trans)
