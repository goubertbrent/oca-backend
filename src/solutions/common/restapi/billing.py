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
from __future__ import unicode_literals

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from google.appengine.ext.deferred import deferred

from mcfw.consts import REST_TYPE_TO
from mcfw.exceptions import HttpBadRequestException
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.rpc.users import get_current_user
from rogerthat.settings import get_server_settings
from rogerthat.utils import send_mail
from shop.dal import get_customer
from shop.models import normalize_vat
from solution_server_settings import get_solution_server_settings
from solutions import translate
from solutions.common.bizz.budget import update_budget
from solutions.common.models.budget import Budget, BudgetTransaction, BudgetOrder, BudgetOrderStatus


@rest('/common/billing/budget', 'get')
@returns(dict)
@arguments()
def api_get_budget():
    budget = Budget.create_key(get_current_user()).get()
    return budget.to_dict() if budget else {'balance': 0}


@rest('/common/billing/budget', 'post', type=REST_TYPE_TO)
@returns(dict)
@arguments(data=dict)
def api_add_budget(data):
    service_user = get_current_user()
    two_weeks_ago = datetime.now() - relativedelta(weeks=2)
    customer = get_customer(service_user)
    try:
        vat = data['vat']
        normalize_vat(customer.country, vat)
    except BusinessException:
        msg = translate(customer.language, 'vat_invalid')
        raise HttpBadRequestException(msg)
    for order in BudgetOrder.list_by_service(service_user.email()):  # type: BudgetOrder
        if order.paid:
            continue
        if order.date > two_weeks_ago:
            raise HttpBadRequestException('You currently cannot order additional views, try again later')
    BudgetOrder(service_email=service_user.email(), status=BudgetOrderStatus.ORDERED).put()
    added_budget = 5000
    updated_budget, transaction = update_budget(service_user, added_budget,
                                                memo='Budget for publishing news and coupons in other city apps')
    deferred.defer(_send_mail_to_admins, service_user, transaction, vat)
    return updated_budget.to_dict()


@rest('/common/billing/budget/transactions', 'get')
@returns([dict])
@arguments()
def api_list_budget_transactions():
    return [t.to_dict() for t in BudgetTransaction.list_by_user(get_current_user())]


def _send_mail_to_admins(service_user, transaction, vat):
    # type: (users.User, BudgetTransaction, str) -> None
    to = get_solution_server_settings().shop_bizz_admin_emails
    from_ = get_server_settings().senderEmail
    subject = 'News budget order %s: %s' % (service_user.email(), transaction.key.id())
    customer = get_customer(service_user)
    body = 'Dear\n\n' \
           'A service has ordered regional news views, please send a 50 EUR invoice to %s.\n\n' \
           'Customer name: %s\n' \
           'Service email: %s\n' \
           'VAT: %s\n\n' \
           'Sent by OCA server.' % (customer.user_email, customer.name, service_user.email(), vat)
    send_mail(from_, to, subject, body, html=None)
