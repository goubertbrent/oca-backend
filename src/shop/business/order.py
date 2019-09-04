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

from StringIO import StringIO
import datetime
import logging

from PIL.Image import Image
import cloudstorage
import dateutil
from dateutil.relativedelta import relativedelta
from google.appengine.ext import db

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.consts import DAY
from rogerthat.models.utils import allocate_id
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import now, get_epoch_from_datetime
from rogerthat.utils.transactions import run_in_xg_transaction, run_in_transaction
from shop import SHOP_JINJA_ENVIRONMENT, SHOP_TEMPLATES_FOLDER
from shop.business.audit import audit_log
from shop.business.legal_entities import get_vat_pct
from shop.business.permissions import user_has_permissions_to_team
from shop.business.service import set_service_disabled
from shop.constants import LOGO_LANGUAGES
from shop.exceptions import NoSubscriptionException, EmptyValueException, \
    OrderAlreadyCanceledException, NoSubscriptionFoundException, ContactNotFoundException, ProductNotFoundException, \
    ProductNotAllowedException, InvalidProductAmountException, InvalidProductQuantityException, \
    MissingProductDependencyException, NoProductsSelectedException
from shop.models import Customer, Order, Quotation, Contact, Product, OrderItem, RegioManagerTeam, QuotationItem, \
    Charge
from solution_server_settings import get_solution_server_settings
from solutions.common.bizz.jobs import delete_solution


@returns(int)
@arguments(customer_id=(int, long))
def get_customer_subscription_length(customer_id):
    customer = Customer.get_by_id(customer_id)
    if not customer.subscription_order_number:
        raise NoSubscriptionFoundException(customer)
    months_till_charge, _ = get_subscription_order_remaining_length(customer_id, customer.subscription_order_number)
    return months_till_charge


@returns(Order)
@arguments(customer_id=(int, long))
def get_subscription_order(customer_id):
    customer = Customer.get_by_id(customer_id)
    if not customer.subscription_order_number:
        raise NoSubscriptionException(customer)
    order = Order.get_by_order_number(customer.id, customer.subscription_order_number)
    if not order.status == Order.STATUS_SIGNED:
        raise BusinessException('The customer his subscription order has not been signed yet.')
    return order


@returns()
@arguments(customer_id=(int, long), next_charge_date=(int, long))
def set_next_charge_date(customer_id, next_charge_date):
    customer = Customer.get_by_id(customer_id)
    if not customer.subscription_order_number:
        raise NoSubscriptionException(customer)
    order = Order.get_by_order_number(customer_id, customer.subscription_order_number)
    if not order.status == Order.STATUS_SIGNED:
        raise BusinessException('The customer his subscription order has not been signed yet.')
    other_orders = Order.list_signed(customer).filter('is_subscription_order', False)  # type: list[Order]
    to_put = [order]
    order.next_charge_date = next_charge_date
    for extension_order in other_orders:
        if extension_order.is_subscription_extension_order:
            extension_order.next_charge_date = next_charge_date
        to_put.append(extension_order)
    db.put(to_put)


@returns(tuple)
@arguments(customer_id=(int, long), subscription_order_number=unicode)
def get_subscription_order_remaining_length(customer_id, subscription_order_number):
    subscription_order = Order.get(Order.create_key(customer_id, subscription_order_number))
    if subscription_order.next_charge_date:
        next_charge_date = subscription_order.next_charge_date + DAY * 14
        try:
            next_charge_datetime = datetime.datetime.utcfromtimestamp(next_charge_date)
        except ValueError:  # Eg. year out of range
            months_till_charge = 1
        else:
            timedelta = dateutil.relativedelta.relativedelta(next_charge_datetime, datetime.datetime.now())
            months_till_charge = timedelta.years * 12 + timedelta.months
            if months_till_charge < 1:
                months_till_charge = 1
    else:
        months_till_charge = 1
    return months_till_charge, subscription_order


@returns()
@arguments(customer_id=(int, long), cancel_reason=unicode, immediately=bool)
def cancel_subscription(customer_id, cancel_reason, immediately=False):
    """
    Marks the customer his subscription as disabled.
    Recurrent billing will disable the service and disconnect all users after the subscription has ended.
    When the 'immediately' parameter is set, the service will be disabled immediately.

    Args:
        customer_id (int, long): Customer id
        cancel_reason (unicode): Reason why the subscription has been canceled.
        immediately (bool): Set to True to disable the service immediately

    Returns: None

    Raises:
        EmptyValueException
        CustomerNotFoundException
        NoSubscriptionException
    """
    if not cancel_reason:
        raise EmptyValueException('cancel_reason')

    customer = Customer.get_by_id(customer_id)

    if not customer.subscription_order_number:
        raise NoSubscriptionException(customer)

    order = Order.get_by_order_number(customer_id, customer.subscription_order_number)
    if immediately or order.status != Order.STATUS_SIGNED:
        def trans():
            try:
                cancel_order(customer, customer.subscription_order_number)
            except OrderAlreadyCanceledException as exception:
                logging.info('Order %s already canceled, continueing...' % exception.order.order_number)

            customer.disabled_reason = cancel_reason
            set_service_disabled(customer, Customer.DISABLED_OTHER)

        run_in_xg_transaction(trans)
    else:
        customer.disabled_reason = cancel_reason
        customer.subscription_cancel_pending_date = now()
        customer.put()


def validate_and_sanitize_order_items(customer, all_products, items):
    # type: (Customer, dict[str, Product], list[OrderItem]) -> None
    if not (len(items) > 0):
        raise NoProductsSelectedException()
    _order_items_signed_orders = []

    def get_order_items_signed_orders():
        if _order_items_signed_orders:
            return _order_items_signed_orders
        for order in Order.list_signed(customer.key()):
            _order_items_signed_orders.extend(OrderItem.list_by_order(order.key()).fetch(None))
        return _order_items_signed_orders

    for item in items:
        product = all_products[item.product]
        if not product:
            raise ProductNotFoundException(item.product)
        elif item.count < 1 or (product.possible_counts and item.count not in product.possible_counts):
            raise InvalidProductAmountException(item.count, item.product)
        if product.organization_types and customer.organization_type not in product.organization_types:
            raise ProductNotAllowedException(product.description(DEFAULT_LANGUAGE))
        item.price = item.price if product.can_change_price else product.price
        if product.product_dependencies:
            for dependency in product.product_dependencies:
                dependency_found = False
                dependencies_product_codes = []
                for dependency in dependency.split('|'):
                    dependency_count = item.count
                    if ':' in dependency:
                        dependency, dependency_count = dependency.split(":")
                        dependency_count = int(dependency_count)
                    dependencies_product_codes.append(dependency)

                    for oi in items:
                        if oi.product == dependency and (dependency_count <= 0 or oi.count == item.count):
                            dependency_found = True
                            break
                    else:
                        # Dependency not found in this order
                        if dependency_count < 0:
                            for oi in get_order_items_signed_orders():
                                if oi.product_code == dependency and (dependency_count <= 0 or oi.number == item.count):
                                    dependency_found = True
                                    break

                if not dependency_found:
                    # for legal entities it is possible that not all possible dependencies exist. so here I take
                    # the first existing dependency to make sure the next lines don't raise a KeyError
                    # it is intentional that it raises a KeyError if none of the dependency products exist
                    for dependency in dependencies_product_codes:
                        if dependency in all_products:
                            break
                    if dependency_count > 0:
                        raise InvalidProductQuantityException(product.description(DEFAULT_LANGUAGE),
                                                              all_products[dependency].description(DEFAULT_LANGUAGE))
                    else:
                        raise MissingProductDependencyException(product.description(DEFAULT_LANGUAGE),
                                                                all_products[dependency].description(DEFAULT_LANGUAGE))


def calculate_order_totals(vat_pct, items, all_products):
    # type: (long, list[OrderItem], dict[str, Product]) -> tuple[float, float, float, float]
    total = 0.0
    for item in items:
        product = all_products[item.product]
        price = item.price if product.can_change_price else product.price
        total += price * item.count
    vat = vat_pct * total / 100
    total_vat_incl = total + vat
    return price, total, vat, total_vat_incl


def create_quotation(customer_id, data, google_user):
    # type: (long, CreateQuotationTO, gusers.User) -> Quotation
    customer_key = Customer.create_key(customer_id)
    contact_key = Contact.create_key(data.contact_id, customer_id)
    customer, contact = db.get((customer_key, contact_key))
    if not contact:
        raise ContactNotFoundException(data.contact_id)
    team = RegioManagerTeam.get_by_id(customer.team_id)
    if google_user:
        azzert(user_has_permissions_to_team(google_user, customer.team_id))
    bucket = get_solution_server_settings().shop_gcs_bucket
    if not bucket:
        raise BusinessException('Shop GCS bucket is not set')
    all_products = {p.code: p for p in Product.list_by_legal_entity(team.legal_entity_id)}
    validate_and_sanitize_order_items(customer, all_products, data.order_items)
    vat_pct = get_vat_pct(customer, team)
    _, total, vat, total_vat_incl = calculate_order_totals(vat_pct, data.order_items, all_products)
    audit_log(customer.id, u"Creating new quotation.")

    def trans():
        quotation_id = allocate_id(Quotation, parent=customer_key)

        quotation_key = Quotation.create_key(quotation_id, customer_id)
        quotation = Quotation(key=quotation_key)
        quotation.contact_id = data.contact_id
        quotation.date = now()
        quotation.vat_pct = vat_pct
        quotation.amount = int(round(total))
        quotation.vat = int(round(vat))
        quotation.total_amount = int(round(total_vat_incl))
        quotation.manager = google_user

        to_put = [quotation]
        number = 0
        order_items = []
        for item in data.order_items:
            number += 1
            order_item = QuotationItem(parent=quotation_key)
            order_item.number = number
            order_item.comment = item.comment
            order_item.product_code = item.product
            order_item.count = item.count
            order_item.price = item.price
            order_items.append(order_item)
        to_put.extend(order_items)
        db.put(to_put)
        pdf_contents = StringIO()
        _generate_order_or_invoice_pdf(None, customer, None, quotation, order_items, pdf_contents, 'order_pdf.html', None,
                                       None, all_products, False, team.legal_entity, contact, is_quotation=True)
        file_name = Quotation.filename(bucket, customer_id, quotation_id)
        with cloudstorage.open(file_name, 'w', content_type='application/pdf') as f:
            f.write(pdf_contents.getvalue())
        return quotation
    return run_in_transaction(trans, xg=True)


def list_quotations(customer_id):
    return Quotation.list(Customer.create_key(customer_id))


def _generate_order_or_invoice_pdf(charge, customer, invoice, order, order_items, output_stream, path, payment_note,
                                   payment_type, products, recurrent, legal_entity, contact, is_quotation=False):
    # type: (Charge, Customer, Invoice, Order, list[OrderItem], StringIO,
    # unicode, unicode, int, dict[str, Product], bool, LegalEntity, Contact)
    # -> None
    from xhtml2pdf import pisa
    for item in order_items:
        item.product_description = products[item.product_code].description(customer.language).replace('\n', '<br />')
        item.product_comment = item.comment or products[item.product_code].default_comment(customer.language) \
            .replace('\n', '<br />')
    if customer.language in LOGO_LANGUAGES:
        logo_path = 'html/img/osa_white_%s_250.jpg' % customer.language
    else:
        logo_path = 'html/img/osa_white_en_250.jpg'
    variables = {
        "customer": customer,
        'legal_entity': legal_entity,
        'contact': contact,
        'language': customer.language,
        "charge": charge,
        "invoice": invoice,
        "order": order,
        "payment_note": payment_note,
        "payment_type": payment_type,
        "order_items": sorted(order_items, key=lambda x: x.number),
        "recurrent": recurrent,
        'logo_path': logo_path,
        'is_quotation': is_quotation
    }
    source_html = SHOP_JINJA_ENVIRONMENT.get_template(path).render(variables)
    # Monkey patch problem in PIL
    orig_to_bytes = getattr(Image, "tobytes", None)
    try:
        if orig_to_bytes is None:
            Image.tobytes = Image.tostring
        pisa.CreatePDF(src=source_html, dest=output_stream, path=SHOP_TEMPLATES_FOLDER)
    finally:
        if orig_to_bytes is None:
            delattr(Image, "tobytes")


@returns(Customer)
@arguments(customer_or_id=(int, long, Customer), order_number=unicode, confirm=bool, delete_service=bool,
           charge_id=(int, long))
def cancel_order(customer_or_id, order_number, confirm=False, delete_service=False, charge_id=None):
    def trans():
        logging.info('Canceling order %s', order_number)
        service_deleted = False
        to_put = list()
        if isinstance(customer_or_id, Customer):
            customer = customer_or_id
            order = db.get(Order.create_key(customer_or_id.id, order_number))
        else:
            customer_id = customer_or_id
            customer, order = db.get((Customer.create_key(customer_id),
                                      Order.create_key(customer_id, order_number)))  # type: Customer, Order

        if order.status == Order.STATUS_CANCELED:
            raise OrderAlreadyCanceledException(order)
        if delete_service and order.is_subscription_order and customer.service_email:
            if confirm:
                delete_solution(users.User(customer.service_email), True)
                service_deleted = True
            else:
                raise BusinessException(
                    "confirm:This will delete the associated application of " + customer.user_email + ". Are you sure you want to continue?")

        order_items = order.list_items()
        if order.status == Order.STATUS_SIGNED:
            if charge_id:
                charge = Charge.get(Charge.create_key(charge_id, order_number, customer.id))
                if not charge:
                    raise BusinessException('Charge with id %s not found' % charge_id)
                if charge.status == Charge.STATUS_EXECUTED:
                    raise BusinessException(
                        'Charge with id %s has already been executed so it cannot be canceled' % charge_id)
                if charge.invoice_number != '':
                    raise BusinessException(
                        'Charge with id %s already has an invoice so it cannot be canceled' % charge_id)
                charge.status = Charge.STATUS_CANCELLED
                charge.date_cancelled = now()
                to_put.append(charge)
            else:
                for charge in Charge.all().ancestor(order).filter("status =", Charge.STATUS_PENDING):
                    charge.status = Charge.STATUS_CANCELLED
                    charge.date_cancelled = now()
                    to_put.append(charge)
            if not order.is_subscription_order:
                extra_months = 0
                products = {p.code: p for p in db.get([Product.create_key(i.product_code) for i in order_items])}
                for item in order_items:
                    product = products[item.product_code]
                    if not product.is_subscription and product.extra_subscription_months > 0:
                        extra_months += product.extra_subscription_months

                if extra_months > 0:
                    logging.info('Substracting %d months from %s\'s subscription' % (extra_months, customer.name))
                    sub_order = Order.get_by_order_number(customer.id, customer.subscription_order_number)
                    next_charge_datetime = datetime.datetime.utcfromtimestamp(
                        sub_order.next_charge_date) - relativedelta(
                        months=extra_months)
                    sub_order.next_charge_date = get_epoch_from_datetime(next_charge_datetime)
                    to_put.append(sub_order)

        order.status = Order.STATUS_CANCELED
        order.date_canceled = now()
        to_put.append(order)
        if order.is_subscription_order:
            if service_deleted:
                customer.service_email = None
                customer.user_email = None
                customer.app_ids = []
            customer.subscription_order_number = None
            to_put.append(customer)
        db.put(to_put)
        return customer

    return run_in_transaction(trans, xg=True)
