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
import json
import logging
from types import NoneType

from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.rpc import arguments, returns
from rogerthat.bizz.service import re_index
from rogerthat.consts import MC_DASHBOARD
from rogerthat.dal.service import get_service_identity, get_default_service_identity
from rogerthat.models import App
from rogerthat.models.news import NewsItem
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.service.api import news
from rogerthat.settings import get_server_settings
from rogerthat.to.news import NewsActionButtonTO, NewsItemTO, NewsItemListResultTO
from rogerthat.utils import now, channel
from rogerthat.utils.service import get_service_identity_tuple
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import update_regiomanager_statistic, get_payed
from shop.business.legal_entities import get_vat_pct
from shop.constants import STORE_MANAGER
from shop.dal import get_customer
from shop.exceptions import NoCreditCardException, AppNotFoundException
from shop.models import Contact, Product, RegioManagerTeam, Order, OrderNumber, OrderItem, Charge
from shop.to import OrderItemTO
from solutions.common.models.news import NewsCoupon
from solutions.common.restapi.store import generate_and_put_order_pdf_and_send_mail


@returns(NewsItemListResultTO)
@arguments(cursor=unicode, service_identity=unicode)
def get_news(cursor=None, service_identity=None):
    return news.list_news(cursor, 20, service_identity)


def _save_coupon_news_id(news_item_id, coupon):
    """
    Args:
        news_item_id (int)
        coupon (NewsCoupon)
    """
    coupon.news_id = news_item_id
    coupon.put()


@returns(NewsItemTO)
@arguments(service_identity_user=users.User, title=unicode, message=unicode, label=unicode, sponsored=bool,
           image=unicode, action_button=(NoneType, NewsActionButtonTO), order_items=(NoneType, [OrderItemTO]),
           news_type=(int, long), qr_code_caption=unicode, app_ids=[unicode], news_id=(NoneType, int, long))
def put_news_item(service_identity_user, title, message, label, sponsored, image, action_button, order_items, news_type,
                  qr_code_caption, app_ids, news_id=None):
    """
    Creates a news item first then processes the payment if necessary (not necessary for non-promoted posts).
    If the payment was unsuccessful it will be retried in a deferred task.
    Args:
        service_identity_user (users.User)
        title (unicode)
        message (unicode)
        label (unicode)
        sponsored (bool)
        image (unicode)
        action_button (NewsActionButtonTO)
        order_items (list of OrderItemTO)
        news_type (int)
        app_ids (list of unicode)
        news_id (long): id of the news item to update. When not provided a new news item will be created.

    Returns:
        NewsItem
    """
    if not order_items or order_items is MISSING:
        order_items = []

    sponsored_until = None
    should_save_coupon = news_type == NewsItem.TYPE_QR_CODE and not news_id
    sponsoring_length = None
    sponsored_app_ids = []
    extra_app_ids = []
    si = get_service_identity(service_identity_user)
    for order_item in reversed(order_items):
        if order_item.product == Product.PRODUCT_NEWS_PROMOTION and sponsored:
            if sponsoring_length and sponsoring_length != order_item.count:
                raise BusinessException('All sponsored order items should have the same count')
            sponsoring_length = order_item.count
            sponsored_until_date = datetime.datetime.utcnow() + datetime.timedelta(days=sponsoring_length)
            sponsored_until = long(sponsored_until_date.strftime('%s'))
            azzert(order_item.app_id)
            azzert(order_item.app_id not in sponsored_app_ids)
            sponsored_app_ids.append(order_item.app_id)
        elif order_item.product == Product.PRODUCT_EXTRA_CITY:
            azzert(order_item.app_id)
            azzert(order_item.app_id not in extra_app_ids)
            extra_app_ids.append(order_item.app_id)
            if order_item.app_id in si.appIds:
                order_items.remove(order_item)
        else:
            raise BusinessException('Invalid product %s' % order_item.product)

    if not news_id and not app_ids:
        raise BusinessException('Please select at least one app to publish this news in')
    if not (order_items or news_id):
        sponsored = False
    if sponsored:
        app_ids = sponsored_app_ids
    service_user, identity = get_service_identity_tuple(service_identity_user)
    if App.APP_ID_ROGERTHAT in si.appIds and App.APP_ID_ROGERTHAT not in app_ids:
        app_ids.append(App.APP_ID_ROGERTHAT)
    kwargs = {
        'sticky': sponsored,
        'sticky_until': sponsored_until,
        'message': message,
        'label': label,
        'service_identity': identity,
        'news_id': news_id,
        'app_ids': app_ids,
        'image': image
    }
    if not news_id:
        kwargs['news_type'] = news_type

    if news_type == NewsItem.TYPE_QR_CODE:
        if should_save_coupon:
            def trans():
                coupon = NewsCoupon(
                    parent=NewsCoupon.create_parent_key(service_identity_user),
                    content=qr_code_caption
                )
                coupon.put()
                return coupon
            coupon = db.run_in_transaction(trans)
            kwargs['qr_code_content'] = u'%s' % json.dumps({'c': coupon.id})
        kwargs['qr_code_caption'] = qr_code_caption
    elif news_type == NewsItem.TYPE_NORMAL:
        kwargs.update({
            'action_button': action_button,
            'title': title
        })
    else:
        raise BusinessException('Invalid news type')
    for key, value in kwargs.items():
        if value is MISSING:
            del kwargs[key]
    with users.set_user(service_user):
        try:
            def trans():
                news_item = news.publish(accept_missing=True, **kwargs)
                if should_save_coupon:
                    _save_coupon_news_id(news_item.id, coupon)
                elif news_type == NewsItem.TYPE_QR_CODE and qr_code_caption is not MISSING and qr_code_caption and news_id:
                    news_coupon = NewsCoupon.get_by_news_id(service_identity_user, news_id)
                    if news_coupon:
                        news_coupon.content = qr_code_caption
                        news_coupon.put()
                    else:
                        logging.warn('Not updating qr_code_caption for non-existing coupon for news with id %d',
                                     news_id)
                if order_items:
                    create_and_pay_news_order(service_user, news_item.id, order_items)
                return news_item

            return run_in_xg_transaction(trans)
        except:
            if should_save_coupon:
                db.delete_async(coupon)
            raise


@returns()
@arguments(service_user=users.User, news_item_id=(int, long), order_items_to=[OrderItemTO])
def create_and_pay_news_order(service_user, news_item_id, order_items_to):
    """
    Creates an order, orderitems, charge and executes the charge. Should be executed in a transaction.
    Args:
        service_user (users.User)
        news_item_id (long)
        order_items_to (ist of OrderItemTO)

    Raises:
        NoCreditCardException
        ProductNotFoundException
    """

    @db.non_transactional
    def _get_customer():
        return get_customer(service_user)

    @db.non_transactional
    def _get_contact():
        return Contact.get_one(customer)

    customer = _get_customer()
    azzert(customer)
    contact = _get_contact()
    azzert(contact)
    if not customer.stripe_valid:
        raise NoCreditCardException(customer)
    extra_city_product_key = Product.create_key(Product.PRODUCT_EXTRA_CITY)
    news_product_key = Product.create_key(Product.PRODUCT_NEWS_PROMOTION)
    rmt_key = RegioManagerTeam.create_key(customer.team_id)
    extra_city_product, news_promotion_product, team = db.get((extra_city_product_key, news_product_key, rmt_key))
    azzert(extra_city_product)
    azzert(news_promotion_product)
    azzert(team)
    new_order_key = Order.create_key(customer.id, OrderNumber.next(team.legal_entity_key))
    vat_pct = get_vat_pct(customer, team)

    total_amount = 0
    added_app_ids = []
    for order_item in order_items_to:
        if order_item.product == Product.PRODUCT_EXTRA_CITY:
            total_amount += extra_city_product.price * order_item.count
            added_app_ids.append(order_item.app_id)
            order_item.price = extra_city_product.price
        elif order_item.product == Product.PRODUCT_NEWS_PROMOTION:
            total_amount += news_promotion_product.price * order_item.count
            order_item.price = news_promotion_product.price
        else:
            raise BusinessException('Invalid product \'%s\'' % order_item.product)
    si = get_default_service_identity(users.User(customer.service_email))
    if added_app_ids:
        keys = [App.create_key(app_id) for app_id in added_app_ids]
        apps = db.get(keys)
        for app_id, app in zip(added_app_ids, apps):
            if not app:
                raise AppNotFoundException(app_id)
            if app_id in si.appIds:
                raise BusinessException('Customer %s already has app_id %s' % (customer.id, app_id))

    vat = int(round(vat_pct * total_amount / 100))
    total_amount_vat_incl = int(round(total_amount + vat))
    now_ = now()
    to_put = []
    order = Order(
        key=new_order_key,
        date=now_,
        amount=total_amount,
        vat_pct=vat_pct,
        vat=vat,
        total_amount=total_amount_vat_incl,
        contact_id=contact.id,
        status=Order.STATUS_SIGNED,
        is_subscription_order=False,
        is_subscription_extension_order=False,
        date_signed=now_,
        manager=STORE_MANAGER,
        team_id=team.id
    )
    to_put.append(order)
    azzert(order.total_amount >= 0)

    for item in order_items_to:
        order_item = OrderItem(
            parent=new_order_key,
            number=item.number,
            product_code=item.product,
            count=item.count,
            comment=item.comment,
            price=item.price
        )
        order_item.app_id = item.app_id
        if order_item.product_code == Product.PRODUCT_NEWS_PROMOTION:
            order_item.news_item_id = news_item_id
        to_put.append(order_item)

    db.put(to_put)

    # Not sure if this is necessary
    deferred.defer(generate_and_put_order_pdf_and_send_mail, customer, new_order_key, service_user,
                   _transactional=True)

    # No need for signing here, immediately create a charge.
    to_put = []
    charge = Charge(parent=new_order_key)
    charge.date = now()
    charge.type = Charge.TYPE_ORDER_DELIVERY
    charge.amount = order.amount
    charge.vat_pct = order.vat_pct
    charge.vat = order.vat
    charge.total_amount = order.total_amount
    charge.manager = order.manager
    charge.team_id = order.team_id
    charge.status = Charge.STATUS_PENDING
    charge.date_executed = now()
    charge.currency_code = team.legal_entity.currency_code
    to_put.append(charge)

    # Update the regiomanager statistics so these kind of orders show up in the monthly statistics
    deferred.defer(update_regiomanager_statistic, gained_value=order.amount / 100,
                   manager=order.manager, _transactional=True)

    # Update the customer service
    si.appIds.extend(added_app_ids)
    to_put.append(si)

    # Update the customer object so the newly added apps are added.
    customer.app_ids.extend(added_app_ids)
    customer.extra_apps_count += len(added_app_ids)
    to_put.append(customer)
    db.put(to_put)
    deferred.defer(re_index, si.user, _transactional=True)

    # charge the credit card
    get_payed(customer.id, order, charge)
    channel.send_message(service_user, 'common.billing.orders.update')
    channel_data = {
        'customer': customer.name,
        'no_manager': True,
        'amount': charge.amount / 100,
        'currency': charge.currency
    }
    server_settings = get_server_settings()
    send_to = server_settings.supportWorkers
    send_to.append(MC_DASHBOARD.email())
    channel.send_message(map(users.User, send_to), 'shop.monitoring.signed_order',
                         info=channel_data)

