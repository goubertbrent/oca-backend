# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import datetime
from types import NoneType

from dateutil.relativedelta import relativedelta
from google.appengine.api import users as gusers
from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from rogerthat.consts import DAY
from rogerthat.rpc.service import BusinessException
from rogerthat.utils import now, get_epoch_from_datetime
from rogerthat.utils.transactions import run_in_xg_transaction
from mcfw.rpc import arguments, returns
from shop.bizz import create_task, is_admin
from shop.business.legal_entities import get_vat_pct
from shop.business.service import set_service_enabled
from shop.exceptions import NoPermissionException
from shop.models import ExpiredSubscription, Prospect, Customer, RegioManagerTeam, ShopTask, Charge, Order, OrderItem, \
    Product


@returns((Charge, NoneType))
@arguments(customer_id=(int, long), status=(int, long))
def set_expired_subscription_status(customer_id, status):
    to_put = list()
    to_delete = list()
    current_user = gusers.get_current_user()
    if not is_admin(current_user):
        raise NoPermissionException('set expired subscription status')
    if not status in ExpiredSubscription.STATUSES or status == ExpiredSubscription.STATUS_EXPIRED:
        raise BusinessException('Invalid expired subscription status (%d)', status)

    def trans():
        charge = None
        expired_subscription, customer = db.get([ExpiredSubscription.create_key(customer_id),
                                                       Customer.create_key(customer_id)])
        expired_subscription.status = status
        expired_subscription.status_updated_timestamp = now()

        if status == ExpiredSubscription.STATUS_WILL_LINK_CREDIT_CARD:
            # Create a task for regiomanager to check if the customer has linked his credit card after two weeks.
            # the ExpiredSubscription object from this customer will be cleaned up in recurrentbilling the day after he has linked it.
            to_put.append(expired_subscription)
            team, prospect = db.get([RegioManagerTeam.create_key(customer.team_id),
                                     Prospect.create_key(customer.prospect_id)])
            execution_time = now() + DAY * 14
            date_string = datetime.datetime.utcfromtimestamp(execution_time).strftime(u'%A %d %b %Y')
            comment = u'Check if the customer has linked his creditcard (for automatic subscription renewal).' \
                      u' If he hasn\'t linked it before %s, contact him again.' % date_string
            task = create_task(current_user.email(), prospect, team.support_manager, execution_time,
                               ShopTask.TYPE_CHECK_CREDIT_CARD, prospect.app_id, comment=comment)
            to_put.append(task)

        elif status == ExpiredSubscription.STATUS_EXTEND_SUBSCRIPTION:
            # Creates a new charge using the customer his subscription order.
            subscription_order, team = db.get([Order.create_key(customer.id, customer.subscription_order_number),
                                               RegioManagerTeam.create_key(customer.team_id)])
            extension_order_item_keys = list()
            order_items = list(OrderItem.list_by_order(subscription_order.key()))
            products_to_get = list()
            for item in order_items:
                products_to_get.append(Product.create_key(item.product_code))
            products = {p.code: p for p in Product.get(products_to_get)}
            # extend per year
            months = 12
            total_amount = 0
            for item in order_items:
                product = products[item.product_code]
                if product.is_subscription and item.price > 0:
                    total_amount += months * item.price
                elif not product.is_subscription and (product.is_subscription_discount or product.extra_subscription_months > 0):
                    total_amount += months * item.price
                elif product.is_subscription_extension:
                    total_amount += months * item.price
                    extension_order_item_keys.append(item.key())

            if total_amount <= 0:
                raise BusinessException('The created charge has a negative amount (%d)' % total_amount)
            next_charge_datetime = datetime.datetime.utcfromtimestamp(now()) + relativedelta(months=months)
            subscription_order.next_charge_date = get_epoch_from_datetime(next_charge_datetime)
            to_put.append(subscription_order)

            # reconnect all previously connected friends if the service was disabled in the past
            if customer.service_disabled_at != 0:
                deferred.defer(set_service_enabled, customer.id, _transactional=True)

            vat_pct = get_vat_pct(customer, team)
            charge = Charge(parent=subscription_order)
            charge.date = now()
            charge.type = Charge.TYPE_SUBSCRIPTION_EXTENSION
            charge.subscription_extension_length = months
            charge.subscription_extension_order_item_keys = extension_order_item_keys
            charge.amount = total_amount
            charge.vat_pct = vat_pct
            charge.vat = int(total_amount * vat_pct / 100)
            charge.total_amount = charge.amount + charge.vat
            charge.currency_code = team.legal_entity.currency_code
            to_put.append(charge)
            to_delete.append(expired_subscription)

        db.put(to_put)
        if to_delete:
            db.delete(to_delete)

        return charge

    return run_in_xg_transaction(trans)


def delete_expired_subscription(customer_id):
    ExpiredSubscription.get_by_customer_id(customer_id).delete()
