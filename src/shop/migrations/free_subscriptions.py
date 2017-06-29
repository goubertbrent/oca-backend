import datetime
import logging

from babel.dates import format_date
from google.appengine.ext import db
from rogerthat.bizz.job import run_job
from shop.bizz import is_signup_enabled, create_order, sign_order
from shop.models import Order, OrderItem, Product
from shop.to import OrderItemTO
from rogerthat.utils import bizz_check
from mcfw.rpc import serialize_complex_value


def job():
    products = Product.get_products_dict()
    paying_subscription_product_codes = [code for code, p in products.iteritems()
                                         if p.is_subscription and p.price and '_' not in p.code]
    run_job(_qry, [Order.STATUS_SIGNED], _replace_subscription_order, [products, paying_subscription_product_codes])


def _qry(status):
    return Order.all(keys_only=True).filter("status", Order.STATUS_SIGNED).filter('is_subscription_order', True)


def _replace_subscription_order(order_key, products, paying_subscription_product_codes):
    customer, old_order = db.get([order_key.parent(), order_key])

    if not is_signup_enabled(customer.app_id):
        logging.debug('FREE_SUBSCRIPTIONS - Signup is not enabled for customer %s with app %s', customer.name, customer.app_id)
        return

    if customer.service_disabled_at != 0:
        logging.debug('FREE_SUBSCRIPTIONS - Customer %s is disabled', customer.name)
        return

    if old_order.status == Order.STATUS_SIGNED:
        order_items = list(OrderItem.all().ancestor(old_order))
        ordered_product_codes = {i.product_code for i in order_items}
        if not ordered_product_codes.intersection(paying_subscription_product_codes):
            logging.debug('FREE_SUBSCRIPTIONS - Customer %s already had a FREE subscription: %s', customer.name, list(ordered_product_codes))
            return

        logging.debug('FREE_SUBSCRIPTIONS - Creating new FREE order for customer %s', customer.name)
        new_order_items = []
        for old_order_item in OrderItem.list_by_order(order_key):
            product = products[old_order_item.product_code]
            if product.is_subscription_extension:
                new_order_items.append(OrderItemTO.create(old_order_item))
        if new_order_items:
            logging.debug('FREE_SUBSCRIPTIONS - Adding %s old order items: %s',
                          len(new_order_items), serialize_complex_value(new_order_items, OrderItemTO, True))

        free_item = OrderItemTO()
        free_item.comment = products[Product.PRODUCT_FREE_SUBSCRIPTION].default_comment(customer.language)

        next_charge_date_time = datetime.datetime.utcfromtimestamp(old_order.next_charge_date)
        language = 'nl' if customer.language == 'nl' else 'en'
        next_charge_date = format_date(next_charge_date_time, locale=language)
        if language == 'nl':
            free_item.comment += u'\n\nEr zijn geen abonnementskosten meer! Uw abonnement is omgezet naar een gratis abonnement.'
            if new_order_items:
                free_item.comment += u'\n\nUw uitbreiding voor extra stad/steden is mee overgezet naar het nieuwe abonnement en zal, zoals bij het oude abonnement, op %s aangerekend worden.' % next_charge_date
        else:
            free_item.comment = u'There are no more subscription costs! Your subscription is changed to a free subscription'
            if new_order_items:
                free_item.comment += u'\n\nThe extension for extra cities is also transferred to the new subscription and will be charged at %s, just like you old subscription.' % next_charge_date

        free_item.count = 1
        free_item.id = None
        free_item.number = 0
        free_item.price = 0
        free_item.product = Product.PRODUCT_FREE_SUBSCRIPTION
        free_item.service_visible_in = None
        new_order_items.append(free_item)

        new_order = create_order(customer, old_order.contact_id, new_order_items, replace=True,
                                 regio_manager_user=old_order.manager)
        new_order.next_charge_date = old_order.next_charge_date
        new_order.put()
    else:
        bizz_check(customer.subscription_order_number != old_order.order_number,
                   'Something is seriously wrong with customer %s (%s)!' % (customer.id, customer.name))
        new_order = Order.get_by_order_number(customer.id, customer.subscription_order_number)

    if new_order.status == Order.STATUS_UNSIGNED and new_order.total_amount > 0:
        logging.debug('FREE_SUBSCRIPTIONS - Signing order %s for customer %s', new_order.order_number, customer.name)
        sign_order(customer.id, new_order.order_number, signature=u'', no_charge=True)
