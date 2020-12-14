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

from mcfw.properties import unicode_property, long_property, bool_property, unicode_list_property, typed_property, \
    float_property, long_list_property
from mcfw.rpc import serialize_complex_value
from rogerthat.models import App
from rogerthat.to import ReturnStatusTO, TO
from rogerthat.to.app import AppInfoTO
from shop.models import Order


class CreateOrderReturnStatusTO(ReturnStatusTO):
    can_replace = bool_property('5')

    @classmethod
    def create(cls, success=True, errormsg=None, can_replace=False):
        r = super(CreateOrderReturnStatusTO, cls).create(success, errormsg)
        r.can_replace = can_replace
        return r


class CompanyTO(object):
    name = unicode_property('1')
    address1 = unicode_property('2')
    address2 = unicode_property('3')
    zip_code = unicode_property('4')
    city = unicode_property('5')
    country = unicode_property('6')
    vat = unicode_property('7')
    organization_type = long_property('8')
    user_email = unicode_property('9')
    telephone = unicode_property('10')
    website = unicode_property('11')
    facebook_page = unicode_property('12')


class CustomerTO(CompanyTO):
    id = long_property('51')
    service_email = unicode_property('52')
    auto_login_url = unicode_property('54')
    migration_job = unicode_property('56')
    manager = unicode_property('57')
    language = unicode_property('61')
    subscription_type = unicode_property('62')
    has_loyalty = bool_property('63')
    creation_time = long_property('64')
    team_id = long_property('65')
    can_edit = bool_property('66')
    is_admin = bool_property('67')
    service_disabled_at = long_property('68')
    service_disabled_reason = unicode_property('69')
    service_disabled_reason_int = long_property('70')
    subscription_cancel_pending_date = long_property('71')
    cancelling_on_date = long_property('72')  # Customer his subscription will be disabled on this date
    community_id = long_property('community_id')

    @staticmethod
    def fromCustomerModel(customer, can_edit, is_admin):
        c = CustomerTO()
        c.name = customer.name
        c.address1 = customer.address1
        c.address2 = customer.address2
        c.zip_code = customer.zip_code
        c.city = customer.city
        c.country = customer.country
        c.vat = customer.vat
        c.organization_type = customer.organization_type
        c.id = customer.id
        c.service_email = customer.service_email
        c.user_email = customer.user_email
        c.auto_login_url = customer.auto_login_url if customer.service_email else None
        c.migration_job = customer.migration_job
        c.manager = customer.manager.email().decode('utf-8') if customer.manager else None
        c.language = customer.language
        c.subscription_type = customer.SUBSCRIPTION_TYPES[customer.subscription_type]
        c.has_loyalty = customer.has_loyalty
        c.creation_time = customer.creation_time
        c.team_id = customer.team_id
        c.can_edit = can_edit
        c.is_admin = is_admin
        c.service_disabled_at = customer.service_disabled_at
        if customer.subscription_cancel_pending_date != 0 and customer.subscription_order_number:
            c.cancelling_on_date = Order.get(
                Order.create_key(customer.id, customer.subscription_order_number)).next_charge_date
        else:
            c.cancelling_on_date = 0
        c.service_disabled_reason = customer.disabled_reason or customer.disabled_reason_str
        c.service_disabled_reason_int = customer.disabled_reason_int
        c.subscription_cancel_pending_date = customer.subscription_cancel_pending_date
        c.website = customer.website
        c.facebook_page = customer.facebook_page
        c.community_id = customer.community_id
        return c


class EmailConsentTO(TO):
    newsletter = bool_property('newsletter')
    email_marketing = bool_property('email_marketing')


class CustomerReturnStatusTO(ReturnStatusTO):
    customer = typed_property('51', CustomerTO)
    warning = unicode_property('52')

    @classmethod
    def create(cls, success=True, errormsg=None, customer=None, warning=None):
        r = super(CustomerReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.customer = customer
        r.warning = warning
        return r


class ChargeTO(object):
    id = long_property('0')
    reference = unicode_property('1')
    amount = long_property('2')  # in euro cents
    order_number = unicode_property('3')
    full_date_str = unicode_property('4')
    last_notification_date_str = unicode_property('5')
    structured_info = unicode_property('6')
    is_recurrent = bool_property('7')
    currency = unicode_property('8')
    total_amount_formatted = unicode_property('9')
    amount_paid_in_advance = long_property('10')
    amount_paid_in_advance_formatted = unicode_property('11')
    status = long_property('12')
    customer_id = long_property('13')
    manager = unicode_property('14')
    customer_po_number = unicode_property('15')
    invoice_number = unicode_property('16')
    paid = bool_property('17')

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (shop.models.Charge): charge db model
        """
        to = cls()
        to.id = model.key().id()
        to.reference = model.reference
        to.amount = model.total_amount
        to.order_number = model.order_number
        to.full_date_str = unicode(model.full_date_str)
        to.last_notification_date_str = unicode(model.last_notification_date_str)
        to.structured_info = model.structured_info
        to.is_recurrent = model.is_recurrent
        to.currency = model.currency
        to.total_amount_formatted = unicode(model.total_amount_formatted)
        to.amount_paid_in_advance = model.amount_paid_in_advance
        to.amount_paid_in_advance_formatted = unicode(model.amount_paid_in_advance_formatted)
        to.status = model.status
        to.customer_id = model.customer_id
        to.manager = model.manager and model.manager.email()
        to.customer_po_number = model.customer_po_number
        to.invoice_number = model.invoice_number
        to.paid = model.paid
        return to


class CustomerChargeTO(object):
    # was a part of SignOrderReturnStatusTO with 51/52
    charge = typed_property('51', ChargeTO, False)
    customer = typed_property('52', CustomerTO, False)

    @classmethod
    def from_model(cls, charge, customer, can_edit=False, is_admin=False):
        to = cls()
        to.charge = ChargeTO.from_model(charge)
        to.customer = CustomerTO.fromCustomerModel(customer, can_edit, is_admin)
        return to


class CustomerChargesTO(object):
    customer_charges = typed_property('1', CustomerChargeTO, True)
    # related to manager/user
    is_admin = bool_property('2')
    is_reseller = bool_property('3')
    is_payment_admin = bool_property('4')

    cursor = unicode_property('5')


class SignOrderReturnStatusTO(ReturnStatusTO, CustomerChargeTO):
    @classmethod
    def create(cls, success=True, errormsg=None, customer=None, charge=None, has_admin_permissions=False):
        r = super(SignOrderReturnStatusTO, cls).create(success, errormsg)
        r.charge = ChargeTO.from_model(charge) if charge else None
        r.customer = CustomerTO.fromCustomerModel(customer, True, has_admin_permissions) if customer else None
        return r


class ContactTO(TO):
    id = long_property('0')
    first_name = unicode_property('1')
    last_name = unicode_property('2')
    email = unicode_property('3')
    phone_number = unicode_property('4')

    @staticmethod
    def fromContactModel(contact):
        c = ContactTO()
        c.id = contact.id
        c.first_name = contact.first_name
        c.last_name = contact.last_name
        c.email = contact.email
        c.phone_number = contact.phone_number
        return c


class SerializableTO(object):
    def __unicode__(self):
        return unicode(serialize_complex_value(self, self.__class__, False))


class OrderItemTO(SerializableTO):
    id = long_property('0')
    number = long_property('1')
    product = unicode_property('2')
    comment = unicode_property('3')
    count = long_property('4')
    price = long_property('5')
    app_id = unicode_property('6')

    @classmethod
    def create(cls, model):
        item = OrderItemTO()
        item.id = model.key().id()
        item.number = model.number
        item.product = model.product.code
        item.comment = model.comment
        item.count = model.count
        item.price = model.price
        item.app_id = getattr(model, 'app_id', None)  # dynamic property
        return item


class CustomerServiceTO(TO):
    email = unicode_property('2', default=None)
    phone_number = unicode_property('4', default=None)
    language = unicode_property('5')
    modules = unicode_list_property('7')
    broadcast_types = unicode_list_property('8')
    organization_type = long_property('10')
    managed_organization_types = long_list_property('13')
    community_id = long_property('community_id')


class ModulesReturnStatusTO(ReturnStatusTO):
    modules = unicode_list_property('51')

    @classmethod
    def create(cls, success=True, errormsg=None, modules=None):
        r = super(ModulesReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.modules = modules or list()
        return r


class OrderTO(TO):
    customer_id = long_property('1')
    order_number = unicode_property('2')
    full_date_str = unicode_property('3')
    full_date_canceled_str = unicode_property('4')
    amount = unicode_property('5')
    next_charge_date = long_property('6')
    can_cancel = bool_property('7')

    @staticmethod
    def fromOrderModel(obj):
        # type: (Order) -> OrderTO
        i = OrderTO()
        i.customer_id = obj.customer_id
        i.order_number = obj.order_number
        i.full_date_str = unicode(obj.full_date_str)
        i.full_date_canceled_str = unicode(obj.full_date_canceled_str)
        i.amount = obj.total_amount_in_euro
        i.next_charge_date = obj.next_charge_date or 0
        i.can_cancel = not obj.is_subscription_order and obj.is_subscription_extension_order and obj.status == Order.STATUS_SIGNED
        return i


class OrderReturnStatusTO(ReturnStatusTO):
    order = typed_property('3', OrderTO, False)

    @classmethod
    def create(cls, success=True, errormsg=None, order=None):
        to = super(OrderReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        to.order = OrderTO.fromOrderModel(order) if order else None
        return to


class InvoiceTO(object):
    customer_id = long_property('1')
    charge_id = long_property('2')
    order_number = unicode_property('3')
    invoice_number = unicode_property('4')
    full_date_str = unicode_property('5')
    paid = bool_property('6')

    @staticmethod
    def fromInvoiceModel(obj):
        i = InvoiceTO()
        i.customer_id = obj.customer_id
        i.charge_id = obj.charge_id
        i.order_number = obj.order_number
        i.invoice_number = obj.invoice_number
        i.full_date_str = unicode(obj.full_date_str)
        i.paid = obj.paid or obj.payment_type in (obj.PAYMENT_MANUAL, obj.PAYMENT_STRIPE, obj.PAYMENT_ON_SITE)
        return i


class SalesStatsInvoiceTO(object):
    amount = long_property('1')
    date = long_property('2')
    operator = unicode_property('3')

    @staticmethod
    def create(obj):
        o = SalesStatsInvoiceTO()
        o.amount = obj.amount
        o.date = obj.date
        o.operator = obj.operator.nickname()
        return o


class OrderAndInvoiceTO(object):
    signed_orders = typed_property("1", OrderTO, True)
    unsigned_orders = typed_property("2", OrderTO, True)
    canceled_orders = typed_property('3', OrderTO, True)
    invoices = typed_property("4", InvoiceTO, True)

    @classmethod
    def create(cls, orders, invoices):
        to = cls()
        to.signed_orders = list()
        to.unsigned_orders = list()
        to.canceled_orders = list()
        to.invoices = map(InvoiceTO.fromInvoiceModel, invoices)
        for order in orders:
            if order.order_number != Order.CUSTOMER_STORE_ORDER_NUMBER:
                if order.status == Order.STATUS_SIGNED:
                    to.signed_orders.append(OrderTO.fromOrderModel(order))
                elif order.status == Order.STATUS_UNSIGNED:
                    to.unsigned_orders.append(OrderTO.fromOrderModel(order))
                elif order.status == Order.STATUS_CANCELED:
                    to.canceled_orders.append(OrderTO.fromOrderModel(order))
        return to


class JobReturnStatusTO(ReturnStatusTO):
    job_key = unicode_property('51')

    @classmethod
    def create(cls, success=True, errormsg=None, job_key=None):
        r = super(JobReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.job_key = job_key
        return r


class JobStatusTO(object):
    progress = long_property('1')
    phase = long_property('2')

    @classmethod
    def from_model(cls, model):
        to = cls()
        to.progress = int(model.estimate_progress())
        to.phase = model.phase
        return to


class PointTO(object):
    lat = float_property('1')
    lon = float_property('2')

    @classmethod
    def create(cls, lat, lon):
        to = cls()
        to.lat = lat
        to.lon = lon
        return to

class RegioManagerBaseTO(object):
    email = unicode_property('1')
    name = unicode_property('2')
    app_ids = unicode_list_property('3')
    show_in_stats = bool_property('4')
    internal_support = bool_property('5')
    phone = unicode_property('6')
    team_id = long_property('7')
    admin = bool_property('8')

    @classmethod
    def from_model(cls, model):
        to = cls()
        to.email = model.email
        to.name = model.name
        to.app_ids = sorted([app_id for app_id in model.app_ids if app_id not in model.read_only_app_ids])
        to.show_in_stats = model.show_in_stats
        to.internal_support = model.internal_support
        to.phone = model.phone
        to.team_id = model.team_id
        to.admin = model.admin
        return to


class RegioManagerTO(RegioManagerBaseTO):
    read_only_app_ids = unicode_list_property('51')

    @classmethod
    def from_model(cls, model):
        to = super(RegioManagerTO, cls).from_model(model)
        to.read_only_app_ids = model.read_only_app_ids
        return to


class RegioManagerReturnStatusTO(ReturnStatusTO):
    regio_manager = typed_property('51', RegioManagerTO, False)

    @classmethod
    def create(cls, success=True, errormsg=None, regio_manager=None):
        to = super(RegioManagerReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        to.regio_manager = RegioManagerTO.from_model(regio_manager) if regio_manager else None
        return to


class AppRightsTO(SerializableTO):
    app_id = unicode_property('1')
    access = unicode_property('2')  # One of RegioManager.ACCESS_*


class RegioManagerTeamTO(object):
    id = long_property('1')
    name = unicode_property('2')
    legal_entity_id = long_property('3')
    app_ids = unicode_list_property('4')
    regio_managers = typed_property('5', RegioManagerTO, True)

    @classmethod
    def from_model(cls, regio_manager_team, regio_managers):
        to = cls()
        to.id = regio_manager_team.id
        to.name = regio_manager_team.name
        to.legal_entity_id = regio_manager_team._legal_entity_id
        to.app_ids = regio_manager_team.app_ids
        to.regio_managers = map(RegioManagerTO.from_model, regio_managers)
        return to


class RegioManagerTeamsTO(object):
    unassigned_regio_managers = typed_property('1', RegioManagerTO, True)
    regio_manager_teams = typed_property('2', RegioManagerTeamTO, True)
    apps = typed_property('3', AppInfoTO, True)
    unassigned_apps = unicode_list_property('4')

    @classmethod
    def from_model(cls, regio_manager_teams, regio_managers, apps):
        to = cls()
        unassigned_regio_managers = []
        rms = {}
        for rm in regio_managers:
            unassigned_regio_managers.append(rm.email)
            rms[rm.email] = rm

        filtered_apps = []
        unassigned_apps = []
        for app in apps:
            if app.app_id != App.APP_ID_OSA_LOYALTY:
                filtered_apps.append(app)
                unassigned_apps.append(app.app_id)

        to.regio_manager_teams = []
        for rmt in regio_manager_teams:
            rmt_members = []
            for rm in rmt.regio_managers:
                unassigned_regio_managers.remove(rm)
                rmt_members.append(rms[rm])
            to.regio_manager_teams.append(RegioManagerTeamTO.from_model(rmt, rmt_members))

            for app_id in rmt.app_ids:
                if app_id in unassigned_apps:
                    unassigned_apps.remove(app_id)

        to.unassigned_regio_managers = map(RegioManagerTO.from_model, [rms[rm] for rm in unassigned_regio_managers])
        to.apps = map(AppInfoTO.fromModel, filtered_apps)
        to.unassigned_apps = sorted(unassigned_apps)
        return to


class RegioManagerStatisticTO(object):
    month_revenue = long_list_property('0')
    manager = unicode_property('1')
    show_in_stats = bool_property('2')
    team_id = long_property('3')

    @classmethod
    def create(cls, model, regio_manager):
        to = cls()
        to.month_revenue = model.month_revenue or list()
        to.manager = model.key().name()
        to.show_in_stats = bool(regio_manager) and regio_manager.show_in_stats
        to.team_id = regio_manager.team_id
        return to


class ShopProductTO(object):
    app_id = unicode_property('0')
    code = unicode_property('1')
    count = long_property('2')

    @classmethod
    def create(cls, app_id, code, count):
        to = cls()
        to.app_id = app_id
        to.code = code
        to.count = count
        return to


class ProductTO(object):
    default = bool_property('0')
    default_comment = unicode_property('1')
    default_count = long_property('2')
    description = unicode_property('3')
    extra_subscription_months = long_property('4')
    is_subscription = bool_property('5')
    is_subscription_discount = bool_property('6')
    module_set = unicode_property('7')
    organization_types = long_list_property('8')
    possible_counts = long_list_property('9')
    price = long_property('10')
    product_dependencies = unicode_list_property('12')
    visible = bool_property('13')
    code = unicode_property('14')
    picture_url = unicode_property('15')
    price_in_euro = unicode_property('16')
    can_change_price = bool_property('17')

    @classmethod
    def create(cls, model, language):
        to = ProductTO()
        to.code = model.key().name()
        to.default = model.default
        to.default_comment = model.default_comment(language)
        to.default_count = model.default_count
        to.description = model.description(language)
        to.extra_subscription_months = model.extra_subscription_months
        to.is_subscription = model.is_subscription
        to.is_subscription_discount = model.is_subscription_discount
        to.module_set = model.module_set
        to.organization_types = model.organization_types
        to.possible_counts = model.possible_counts
        to.price = model.price
        to.product_dependencies = model.product_dependencies
        to.visible = model.visible
        to.picture_url = model.picture_url
        to.price_in_euro = model.price_in_euro
        to.can_change_price = model.can_change_price
        return to


class OrderItemReturnStatusTO(ReturnStatusTO):
    order_item = typed_property('5', OrderItemTO)

    @classmethod
    def create(cls, success=True, errormsg=None, order_item=None):
        r = super(OrderItemReturnStatusTO, cls).create(success, errormsg)
        if order_item:
            r.order_item = OrderItemTO.create(order_item)
        else:
            r.order_item = None
        return r


class BoolReturnStatusTO(ReturnStatusTO):
    bool = bool_property('5')

    @classmethod
    def create(cls, success=True, errormsg=None, bool_value=False):
        r = super(BoolReturnStatusTO, cls).create(success, errormsg)
        r.bool = bool_value
        return r


class SimpleAppTO(object):
    id = unicode_property('0')
    name = unicode_property('1')

    @classmethod
    def from_model(cls, model):
        app = cls()
        app.id = model.app_id
        app.name = model.name
        return app


class SubscriptionLengthReturnStatusTO(ReturnStatusTO):
    subscription_length = long_property('3')

    @classmethod
    def create(cls, success=True, errormsg=None, subscription_length=0):
        to = super(SubscriptionLengthReturnStatusTO, cls).create(success, errormsg)
        to.subscription_length = subscription_length
        return to


class LegalEntityTO(object):
    id = long_property('1')
    name = unicode_property('2')
    address = unicode_property('3')
    postal_code = unicode_property('4')
    city = unicode_property('5')
    country_code = unicode_property('6')
    phone = unicode_property('7')
    email = unicode_property('8')
    vat_percent = long_property('9')
    vat_number = unicode_property('10')
    iban = unicode_property('11')
    bic = unicode_property('12')
    terms_of_use = unicode_property('13')
    is_mobicage = bool_property('14')
    currency = unicode_property('15')
    currency_code = unicode_property('16')
    revenue_percentage = long_property('17')

    @classmethod
    def from_model(cls, model):
        to = cls()
        to.id = model.key().id()
        to.name = model.name
        to.address = model.address
        to.postal_code = model.postal_code
        to.city = model.city
        to.country_code = model.country_code
        to.phone = model.phone
        to.email = model.email
        to.vat_percent = model.vat_percent
        to.vat_number = model.vat_number
        to.iban = model.iban
        to.bic = model.bic
        to.terms_of_use = model.terms_of_use
        to.is_mobicage = model.is_mobicage
        to.currency = model.currency
        to.currency_code = model.currency_code
        to.revenue_percentage = model.revenue_percentage
        return to


class LegalEntityReturnStatusTO(ReturnStatusTO):
    entity = typed_property('101', LegalEntityTO, False)

    @classmethod
    def create(cls, success=True, errormsg=None, entity=None):
        to = super(LegalEntityReturnStatusTO, cls).create(success, errormsg)
        to.entity = LegalEntityTO.from_model(entity) if entity else None
        return to


class CustomerLocationTO(object):
    name = unicode_property('1')
    description = unicode_property('2')
    has_terminal = bool_property('3')
    lat = float_property('4')
    lon = float_property('5')
    address = unicode_property('6')
    type = long_property('7')

    def __init__(self, name=None, description=None, has_terminal=False, lat=None, lon=None, address=None, type_=None):
        self.name = name
        self.description = description
        self.has_terminal = has_terminal
        self.lat = lat
        self.lon = lon
        self.address = address
        self.type = type_


class ImportCustomersReturnStatusTO(ReturnStatusTO):
    customer_count = long_property('101')

    @classmethod
    def create(cls, success=True, errormsg=None, customer_count=0):
        status = super(ImportCustomersReturnStatusTO, cls).create(success, errormsg)
        status.customer_count = customer_count
        return status
