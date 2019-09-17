from contextlib import closing
import logging

from google.appengine.ext import deferred, db, ndb

from mcfw.properties import azzert
from rogerthat.utils import now, channel, today, send_mail
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import create_task, broadcast_task_updates, \
    generate_order_or_invoice_pdf, send_order_email, \
    update_regiomanager_statistic
from shop.business.i18n import shop_translate
from shop.business.legal_entities import get_vat_pct
from shop.business.prospect import create_prospect_from_customer
from shop.constants import STORE_MANAGER
from shop.dal import get_customer
from shop.models import StripePayment, RegioManagerTeam, Contact, Order, \
    OrderNumber, Customer, Prospect, ShopTask, Product, OrderItem
from solution_server_settings import get_solution_server_settings
from solutions.common.bizz.budget import update_budget
from solutions.common.dal import get_solution_settings

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

CREATE_SHOPTASK_FOR_ITEMS = [Product.PRODUCT_ROLLUP_BANNER, Product.PRODUCT_CARDS]


@ndb.transactional()
def stripe_order_completed(session_id):
    payment = StripePayment.create_key(session_id).get()
    azzert(payment, u'Payment not found')
    azzert(payment.status == StripePayment.STATUS_CREATED, u'Payment status incorrect')
    payment.status = StripePayment.STATUS_COMPLETED
    payment.put()

    deferred.defer(_stripe_order_completed, session_id, _transactional=True)


def _stripe_order_completed(session_id):
    payment = StripePayment.create_key(session_id).get()
    service_user = payment.service_user

    language = get_solution_settings(service_user).main_language
    customer = get_customer(service_user)
    azzert(customer)
    contact = Contact.get_one(customer)
    azzert(contact)
    team = RegioManagerTeam.get(RegioManagerTeam.create_key(customer.team_id))
    azzert(team)

    vat_pct = get_vat_pct(customer, team)
    all_products = {product.code: product for product in Product.get([Product.create_key(item.product_code)
                                                                      for item in payment.items])}

    def trans():
        old_order_key = Order.create_key(customer.id, Order.CUSTOMER_STORE_ORDER_NUMBER)
        old_order = db.get(old_order_key)
        
        now_ = now()
        to_put = []
        to_delete = [old_order]
        for old_item in OrderItem.list_by_order(old_order_key):
            to_delete.append(old_item)

        order_number = OrderNumber.next(team.legal_entity_key)
        new_order_key = Order.create_key(customer.id, order_number)
        new_order = Order(key=new_order_key)
        new_order.contact_id = contact.key().id()
        new_order.date = now_
        new_order.amount = 0
        new_order.vat = 0
        new_order.vat_pct = vat_pct
        new_order.total_amount = 0
        new_order.status = Order.STATUS_SIGNED
        new_order.is_subscription_order = False
        new_order.is_subscription_extension_order = False
        new_order.date_signed = now_
        new_order.manager = STORE_MANAGER
        new_order.team_id = team.id

        number = 0
        added_budget = 0
        budget_description = None
        should_create_shoptask = False
        for item in payment.items:
            product = all_products[item.product_code]
            number += 1
            order_item = OrderItem(parent=new_order)
            order_item.number = number
            order_item.comment = product.default_comment(language)
            order_item.product_code = item.product_code
            order_item.count = item.count
            order_item.price = product.price
            to_put.append(order_item)

            new_order.amount += order_item.price * order_item.count
            
            if item.product_code in CREATE_SHOPTASK_FOR_ITEMS:
                should_create_shoptask = True

            if item.product_code == Product.PRODUCT_BUDGET:
                added_budget += order_item.price * order_item.count
                budget_description = product.description(language)

        if added_budget:
            deferred.defer(update_budget, service_user, added_budget, service_identity=None, context_type=None,
                           context_key=None, memo=budget_description, _transactional=True)

        new_order.vat = int(round(vat_pct * new_order.amount / 100))
        new_order.total_amount = int(round(new_order.amount + new_order.vat))

        to_put.append(new_order)

        db.put(to_put)
        db.delete(to_delete)

        deferred.defer(generate_and_put_order_pdf_and_send_mail, customer, new_order_key, service_user,
                       contact, _transactional=True)
        deferred.defer(contact_support_new_invoice_to_be_created, customer, order_number, contact,
                       _transactional=True)

        # Update the regiomanager statistics so these kind of orders show up in the monthly statistics
        deferred.defer(update_regiomanager_statistic, gained_value=new_order.amount / 100,
                       manager=new_order.manager, _transactional=True)

        channel.send_message(service_user, 'solutions.common.orders.update')
        channel.send_message(service_user, 'solutions.common.shop.reload')
        if should_create_shoptask:
            deferred.defer(create_task_for_order, customer.id, new_order.order_number, _countdown=5,
                           _transactional=True)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


def generate_and_put_order_pdf_and_send_mail(customer, new_order_key, service_user, contact=None):
    def trans():
        new_order = Order.get(new_order_key)
        with closing(StringIO()) as pdf:
            generate_order_or_invoice_pdf(pdf, customer, new_order, contact or new_order.contact)
            new_order.pdf = pdf.getvalue()

        new_order.put()
        deferred.defer(send_order_email, new_order_key, service_user, _transactional=True)

    run_in_xg_transaction(trans)


def contact_support_new_invoice_to_be_created(customer, order_number, contact):
    sln_server_settings = get_solution_server_settings()
    logging.debug('Sending mail to support')
    send_mail(sln_server_settings.shop_billing_email,
              customer.team.support_manager,
              u'New manual invoice to be created',
              u'A new invoice has to be created and sent to customer %s (%s). See order %s for more details.'
              % (customer.name, customer.id, order_number))
    logging.debug('Sending mail to customer')

    to = [contact.email]
    to.extend(sln_server_settings.shop_payment_admin_emails)

    with closing(StringIO()) as sb:
        sb.write(shop_translate(customer.language, 'dear_name',
                                name="%s %s" % (contact.first_name, contact.last_name)).encode('utf-8'))
        sb.write('\n\n')
        sb.write(shop_translate(customer.language, 'manual_invoice_will_be_created',
                                contact_email=sln_server_settings.shop_reply_to_email).encode('utf-8'))
        sb.write('\n\n')
        sb.write(shop_translate(customer.language, 'with_regards').encode('utf-8'))
        sb.write('\n')
        sb.write(shop_translate(customer.language, 'the_osa_team').encode('utf-8'))
        body = sb.getvalue()

    subject = '%s %s' % (shop_translate(customer.language, 'order_number'), order_number)
    send_mail(sln_server_settings.shop_billing_email, to, subject, body)


def create_task_for_order(customer_id, order_number):
    customer = Customer.get_by_id(customer_id)
    prospect_id = customer.prospect_id
    if prospect_id is None:
        prospect = create_prospect_from_customer(customer)
        prospect_id = prospect.id
    team, prospect = db.get(
        [RegioManagerTeam.create_key(customer.team_id), Prospect.create_key(prospect_id)])
    azzert(team.support_manager, u'No support manager found for team %s' % team.name)
    comment = u'Customer placed a new order: %s' % order_number
    task = create_task(
        created_by=STORE_MANAGER.email(),
        prospect_or_key=prospect,
        app_id=prospect.app_id,
        status=ShopTask.STATUS_NEW,
        task_type=ShopTask.TYPE_SUPPORT_NEEDED,
        address=None,
        assignee=team.support_manager,
        comment=comment,
        execution_time=today() + 86400 + 11 * 3600,  # tomorrow at 11:00
        notify_by_email=True
    )
    task.put()
    broadcast_task_updates([team.support_manager])
