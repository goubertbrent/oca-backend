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

import base64
import datetime
import json
import logging
import re
import time
import urllib

from babel import Locale
from babel.dates import format_date, get_timezone
from babel.numbers import get_currency_symbol, format_currency
from dateutil.relativedelta import relativedelta
from google.appengine.api import users as gusers, images
from google.appengine.ext import db, blobstore, ndb
from oauth2client.contrib.appengine import CredentialsProperty

from mcfw.cache import CachedModelMixIn, invalidate_cache
from mcfw.properties import azzert
from mcfw.serialization import deserializer, ds_model, serializer, s_model, register
from mcfw.utils import chunks, Enum
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.consts import DAY
from rogerthat.models import ServiceProfile
from rogerthat.models.common import NdbModel
from rogerthat.rpc import users
from rogerthat.utils import bizz_check, get_epoch_from_datetime, now
from shop.business.i18n import SHOP_DEFAULT_LANGUAGE, shop_translate
from shop.exceptions import CustomerNotFoundException, NoSupportManagerException
from solutions.common.bizz import OrganizationType, SolutionModule


def _normalize_vat_be(vat):
    vat = vat.strip().upper()
    country_code = vat[:2]
    bizz_check(country_code == "BE", "This is not a Belgian VAT number (BE 0123 456 789).")
    vat = vat[2:]
    vat = "".join((c for c in vat if c in "1234567890"))
    if len(vat) == 9:
        vat = '0' + vat
    vat = country_code + vat
    bizz_check(len(vat) == 12, "This vat number could not be validated for Belgium (BE 0123 456 789).")
    return vat


def _normalize_vat_nl(vat):
    vat = vat.strip().upper()
    country_code = vat[:2]
    bizz_check(country_code == "NL", "This is not a Dutch VAT number (NL999999999B99).")
    logging.info("vat: " + vat)
    vat = vat[2:]
    logging.info("vat: " + vat)
    vat = "".join((c for c in vat if c in "1234567890B"))
    logging.info("vat: " + vat)
    vat = country_code + vat
    bizz_check(re.match("NL[1234567890]{9,9}B[1234567890]{2,2}", vat),
               "This vat number could not be validated for the Netherlands (NL999999999B99).")
    return vat


def _normalize_vat_fr(vat):
    vat = vat.strip().upper()
    country_code = vat[:2]
    bizz_check(country_code == "FR", "This is not a French VAT number (FR99 999999999).")
    vat = vat[2:]
    vat = "".join((c for c in vat if c in "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    vat = country_code + vat
    bizz_check(len(vat) == 13, "This vat number could not be validated for France (FR99 999999999).")
    return vat


def _normalize_vat_es(vat):
    vat = vat.strip().upper()
    country_code = vat[:2]
    bizz_check(country_code == "ES", "This is not a Spanish VAT number (ES99 999999999).")
    vat = vat[2:]
    vat = "".join((c for c in vat if c in "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    vat = country_code + vat
    bizz_check(len(vat) == 11, "This vat number could not be validated for Spain (ES99 999999999).")
    return vat


_vat_validators = dict(BE=_normalize_vat_be,
                       NL=_normalize_vat_nl,
                       FR=_normalize_vat_fr,
                       ES=_normalize_vat_es)


def normalize_vat(country, vat):
    bizz_check(country in _vat_validators, "VAT validation is not supported for country " + country)
    return _vat_validators[country](vat)


class RegioManagerTeam(db.Model):
    name = db.StringProperty(indexed=False)
    app_ids = db.StringListProperty(indexed=True)
    regio_managers = db.StringListProperty(indexed=False)
    support_manager = db.StringProperty(indexed=False)
    legal_entity_id = db.IntegerProperty(indexed=True)
    is_mobicage = db.BooleanProperty(default=False)

    @property
    def id(self):
        return self.key().id()

    @property
    def legal_entity(self):
        if not hasattr(self, '_legal_entity'):
            if self.legal_entity_id is None:
                self._legal_entity = LegalEntity.get_mobicage()
            else:
                self._legal_entity = LegalEntity.get_by_id(self.legal_entity_id)

        return self._legal_entity

    @property
    def legal_entity_key(self):
        return LegalEntity.create_key(
            self.legal_entity_id) if self.legal_entity_id else LegalEntity.get_mobicage().key()

    @classmethod
    def create_key(cls, team_id):
        return db.Key.from_path(cls.kind(), team_id)

    @classmethod
    def get_by_app_id(cls, app_id):
        return cls.all().filter('app_ids =', app_id).get()

    def get_support(self):
        if not self.support_manager:
            raise NoSupportManagerException(self)
        return RegioManager.get(RegioManager.create_key(self.support_manager))

    @classmethod
    def get_mobicage(cls):
        return cls.all().filter('is_mobicage', True).get()

    @classmethod
    def list_all(cls):
        return cls.all()


class RegioManager(db.Model):
    """
    Note:
        Key is the email of this manager.
    """
    ACCESS_NO = "no"
    ACCESS_READ_ONLY = "read-only"
    ACCESS_FULL = "full"

    name = db.StringProperty()
    app_ids = db.StringListProperty()  # complete list with supported app_ids
    read_only_app_ids = db.StringListProperty()  # subset of app_ids
    show_in_stats = db.BooleanProperty(default=True, indexed=False)
    internal_support = db.BooleanProperty(default=False)
    phone = db.StringProperty(indexed=False)
    credentials = CredentialsProperty(indexed=False)  # type: Credentials
    team_id = db.IntegerProperty(indexed=True)
    admin = db.BooleanProperty(default=False, indexed=False)

    @property
    def user(self):
        return gusers.User(self.email)

    @property
    def email(self):
        return self.key().name()

    @property
    def full_app_ids(self):
        return [app_id for app_id in self.app_ids if app_id not in self.read_only_app_ids]

    @classmethod
    def list_by_app_id(cls, app_id):
        return cls.all().filter('app_ids =', app_id).order('name')

    @classmethod
    def create_key(cls, email):
        return db.Key.from_path(cls.kind(), email)

    def has_access(self, team_id):
        if self.team_id == team_id:
            return self.ACCESS_FULL
        return self.ACCESS_READ_ONLY

    def grant(self, app_id, access):
        if access == self.ACCESS_READ_ONLY:
            if app_id not in self.app_ids:
                self.app_ids.append(app_id)
            if app_id not in self.read_only_app_ids:
                self.read_only_app_ids.append(app_id)
        elif access == self.ACCESS_FULL:
            if app_id not in self.app_ids:
                self.app_ids.append(app_id)
            if app_id in self.read_only_app_ids:
                self.read_only_app_ids.remove(app_id)

    def revoke(self, app_id):
        if app_id in self.read_only_app_ids:
            self.read_only_app_ids.remove(app_id)
        if app_id in self.app_ids:
            self.app_ids.remove(app_id)

    @property
    def team(self):
        if not hasattr(self, '_team'):
            self._team = RegioManagerTeam.get_by_id(self.team_id)
        return self._team


class Product(db.Model):
    PRODUCT_BUDGET = u'BDGT'
    PRODUCT_ACTION_3_EXTRA_CITIES = u'A3CT'
    PRODUCT_SUBSCRIPTION_ASSOCIATION = u'SJUP'
    PRODUCT_ROLLUP_BANNER = u'BNNR'
    PRODUCT_FLYERS = u'POSM'
    PRODUCT_DEMO = u'DEMO'
    PRODUCT_FREE_PRESENCE = u'OCAP'
    PRODUCT_ONE_TIME_CREDIT_CARD_PAYMENT_DISCOUNT = u'CRED'
    PRODUCT_CARDS = u'KKRT'
    PRODUCT_NEWS_PROMOTION = u'NEWS'
    PRODUCT_FREE_SUBSCRIPTION = u'FREE'
    price = db.IntegerProperty()  # In euro cents
    default_count = db.IntegerProperty()
    default = db.BooleanProperty()
    possible_counts = db.ListProperty(int)
    is_subscription = db.BooleanProperty()
    is_subscription_discount = db.BooleanProperty()
    is_subscription_extension = db.BooleanProperty(default=False, indexed=False)
    module_set = db.StringProperty()
    organization_types = db.ListProperty(int)
    product_dependencies = db.StringListProperty()
    visible = db.BooleanProperty(default=False)
    extra_subscription_months = db.IntegerProperty(default=0)
    picture_url = db.StringProperty(default="", indexed=False)

    is_multilanguage = db.BooleanProperty(default=True, indexed=False)
    # when None: product_code.default_comment translation key is used. (see method default_comment)
    # Set to empty string to return an empty string as translation.
    default_comment_translation_key = db.StringProperty(indexed=False)
    # Same as above
    description_translation_key = db.StringProperty(indexed=False)
    legal_entity_id = db.IntegerProperty()
    can_change_price = db.BooleanProperty(default=False, indexed=False)

    @property
    def code(self):
        return self.key().name()

    def default_comment(self, language):
        if self.default_comment_translation_key is None:
            return shop_translate(language, u"%s.default_comment" % self.code)

        if self.is_multilanguage and self.default_comment_translation_key:
            return shop_translate(language, self.default_comment_translation_key)

        return self.default_comment_translation_key

    def description(self, language):
        if self.description_translation_key is None:
            return shop_translate(language, u"%s.description" % self.code)

        if self.is_multilanguage and self.description_translation_key:
            return shop_translate(language, self.description_translation_key)

        return self.description_translation_key

    @property
    def price_in_euro(self):
        return u'{:20,.2f}'.format(self.price / 100.0)

    def format_price(self, currency, locale=SHOP_DEFAULT_LANGUAGE, ratio=1.0, **kwargs):
        return format_currency(self.price * ratio / 100.0, currency, locale=locale, **kwargs)

    @staticmethod
    def get_by_code(code):
        return Product.get_by_key_name(code)

    @classmethod
    def create_key(cls, code):
        return db.Key.from_path(cls.kind(), code)

    @classmethod
    @db.non_transactional
    def get_products_dict(cls):
        return {p.code: p for p in cls.all()}

    @classmethod
    def list_by_legal_entity(cls, legal_entity_id):
        from shop.dal import get_mobicage_legal_entity
        legal_entity_id = legal_entity_id if legal_entity_id else get_mobicage_legal_entity().key().id()
        return cls.all().filter('legal_entity_id', legal_entity_id)

    @classmethod
    def list_visible_by_legal_entity(cls, legal_entity_id):
        return cls.all().filter("visible =", True).filter('legal_entity_id', legal_entity_id)


class Customer(db.Model):
    vat = db.StringProperty()
    name = db.StringProperty()
    normalized_name = db.StringProperty()
    creation_time = db.IntegerProperty(default=0)
    address1 = db.StringProperty()
    address2 = db.StringProperty()
    zip_code = db.StringProperty()
    city = db.StringProperty()
    country = db.StringProperty()
    language = db.StringProperty(indexed=False)
    user_email = db.StringProperty()
    service_email = db.StringProperty()
    manager = db.UserProperty(indexed=False)
    subscription_order_number = db.StringProperty()
    organization_type = db.IntegerProperty(default=ServiceProfile.ORGANIZATION_TYPE_PROFIT)
    managed_organization_types = db.ListProperty(int, indexed=False)
    migration_job = db.StringProperty(indexed=False)
    default_app_id = db.StringProperty()  # TODO communities: remove after migration
    community_id = db.IntegerProperty()
    subscription_type = db.IntegerProperty(indexed=False, default=-1)
    has_loyalty = db.BooleanProperty(indexed=False, default=False)
    team_id = db.IntegerProperty(indexed=False)
    website = db.StringProperty()
    facebook_page = db.StringProperty()
    # when set to anything lower than the current date that isn't 0, the
    # service of the customer will be disabled over night.
    subscription_cancel_pending_date = db.IntegerProperty(default=0)
    service_disabled_at = db.IntegerProperty(default=0)  # 0 = not disabled
    disabled_reason = db.StringProperty(indexed=False)
    disabled_reason_int = db.IntegerProperty(default=0)

    stripe_id = db.StringProperty()  # todo remove deprecated
    stripe_id_created = db.IntegerProperty(default=0)  # todo remove deprecated
    stripe_credit_card_id = db.StringProperty()  # todo remove deprecated

    SUBSCRIPTION_TYPE_NONE = -1
    SUBSCRIPTION_TYPE_STATIC = 0
    SUBSCRIPTION_TYPE_DYNAMIC = 1
    SUBSCRIPTION_TYPES = {
        SUBSCRIPTION_TYPE_NONE: u'No subscription',
        SUBSCRIPTION_TYPE_STATIC: u'Static',
        SUBSCRIPTION_TYPE_DYNAMIC: u'Dynamic'
    }

    DISABLED_SUBSCRIPTION_EXPIRED = 1  # deprecated
    DISABLED_BAD_PAYER = 2  # deprecated
    DISABLED_OTHER = 3
    DISABLED_BY_CITY = 4

    DISABLED_REASONS = {
        DISABLED_SUBSCRIPTION_EXPIRED: u'Subscription expired',
        DISABLED_BAD_PAYER: u'Did not pay on time',
        DISABLED_OTHER: u'Other',
        DISABLED_BY_CITY: u'Disabled by city'
    }

    @property
    def service_user(self):
        return users.User(self.service_email) if self.service_email else None

    @property
    def country_str(self):
        return Locale(self.language).territories[self.country]

    @property
    def id(self):
        return self.key().id()

    @property
    def app_id(self):
        # TODO communities: remove after migration
        if self.default_app_id:
            return self.default_app_id
        if self.app_ids:
            return self.app_ids[0]
        return None

    @property
    def locale(self):
        if self.language == 'en':
            return 'en_GB'
        elif self.language == 'nl':
            return 'nl_BE'
        return self.language

    @classmethod
    def list_by_name(cls, name, limit=20):
        return cls.all().filter('name =', name).fetch(limit)

    @classmethod
    def create_key(cls, customer_id):
        azzert(isinstance(customer_id, (int, long)))
        return db.Key.from_path(cls.kind(), customer_id)

    @classmethod
    def starting_with(cls, name):
        name = cls.normalize_name(name)
        return cls.all().filter('normalized_name >=', name).filter('normalized_name <', name + u'\ufffd').order(
            'normalized_name').fetch(20)

    @staticmethod
    def normalize_name(name):
        return "".join((c for c in name.strip().lower() if c in "abcdefghijklmnopqrstuvwxyz"))

    def list_contacts(self):
        return Contact.list(self.key())

    @property
    def auto_login_url(self):
        return u"/internal/shop/login_as?%s" % urllib.urlencode({"customer_id": self.id})

    @classmethod
    def get_by_service_email(cls, service_email):
        return cls.all().filter('service_email', service_email).get()

    @classmethod
    def list_by_user_email(cls, user_email):
        return cls.all().filter('user_email', user_email)

    @classmethod
    def list_enabled_by_organization_type_in_community(cls, community_id, organization_type):
        return cls.all().filter('community_id', community_id) \
            .filter('service_disabled_at', 0) \
            .filter('organization_type', organization_type) \
            .order('name')

    @classmethod
    def list_by_community_id(cls, community_id):
        return cls.all().filter('community_id', community_id)

    @property
    def disabled_reason_str(self):
        if self.disabled_reason_int == 0:
            return u'subscription not disabled'
        else:
            return self.DISABLED_REASONS[self.disabled_reason_int]

    @property
    def team(self):
        if not hasattr(self, '_team'):
            self._team = RegioManagerTeam.get_by_id(self.team_id)
        return self._team

    @property
    def legal_entity(self):
        if not hasattr(self, '_legal_entity'):
            self._legal_entity = self.team.legal_entity
        return self._legal_entity

    @classmethod
    def get_by_id(cls, ids, parent=None, **kwargs):
        """Get instance(s) of Customer by id.

        Args:
          ids: A single id or a list or tuple of ids.
          parent: Parent of instances to get.  Can be a model or key.
          config: datastore_rpc.Configuration to use for this request.

        Raises:
            CustomerNotFoundException: When the customer is not found (only when a single id was specified)

        Returns:
            Customer

        """
        customer = super(Customer, cls).get_by_id(ids, parent, **kwargs)
        if not customer and not isinstance(customer, list):
            raise CustomerNotFoundException(ids)
        return customer

    @property
    def should_pay_vat(self):
        return not self.vat or self.country == self.legal_entity.country_code

    @classmethod
    def list_by_app_id(cls, app_id):
        return Customer.all().filter('app_ids', app_id)

    @property
    def editable_organization_types(self):
        """
            The organization types of the services that this service can create/edit via the dashboard
        Returns:

        """
        if self.managed_organization_types:
            allowed_types = list(self.managed_organization_types)
            if ServiceProfile.ORGANIZATION_TYPE_CITY in allowed_types:
                allowed_types.remove(ServiceProfile.ORGANIZATION_TYPE_CITY)
            if allowed_types:
                return allowed_types

        return [ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT,
                ServiceProfile.ORGANIZATION_TYPE_PROFIT,
                ServiceProfile.ORGANIZATION_TYPE_EMERGENCY]

    def can_only_edit_organization_type(self, organization_type):
        return len(self.editable_organization_types) == 1 and self.editable_organization_types[0] == organization_type

    def can_edit_service(self):
        """Check if a city service can edit another service on dashboard (merchants...etc)."""
        return self.organization_type == OrganizationType.CITY

    @property
    def full_address_string(self):
        return ', '.join([' '.join([self.address1 or '', self.address2 or '']),
                          self.zip_code,
                          self.city])


class CustomerSignupStatus(Enum):
    PENDING = 0
    APPROVED = 1
    DENIED = 2


class CustomerSignup(db.Model):
    EXPIRE_TIME = DAY * 3
    DEFAULT_MODULES = [
        SolutionModule.NEWS,
        SolutionModule.QR_CODES,
        SolutionModule.STATIC_CONTENT,
        SolutionModule.WHEN_WHERE,
        SolutionModule.ASK_QUESTION,
        SolutionModule.BILLING
    ]

    company_name = db.StringProperty()
    company_organization_type = db.IntegerProperty()
    company_address1 = db.StringProperty()
    company_zip_code = db.StringProperty()
    company_city = db.StringProperty()
    company_vat = db.StringProperty()
    company_email = db.StringProperty()
    company_telephone = db.StringProperty()
    company_website = db.StringProperty()
    company_facebook_page = db.StringProperty()

    customer_name = db.StringProperty()
    customer_address1 = db.StringProperty()
    customer_zip_code = db.StringProperty()
    customer_city = db.StringProperty()
    customer_email = db.StringProperty()
    customer_telephone = db.StringProperty()
    customer_website = db.StringProperty()
    customer_facebook_page = db.StringProperty()

    language = db.StringProperty()
    timestamp = db.IntegerProperty()
    service_email = db.StringProperty(default=None)  # Set when created via the new way
    done = db.BooleanProperty(indexed=True, default=False)
    inbox_message_key = db.StringProperty(indexed=True)
    status = db.IntegerProperty(default=CustomerSignupStatus.PENDING)

    @classmethod
    def list_pending_by_customer_email(cls, email):
        return cls.all().filter('done', False).filter('customer_email', email)

    @staticmethod
    def normalize(value):
        if not isinstance(value, unicode):
            value = unicode(value)
        return ''.join(value.lower().split())

    def is_same_signup(self, signup):
        for prop_name, _ in self.properties().iteritems():
            if prop_name.startswith('company') or prop_name.startswith('customer'):
                value = self.normalize(getattr(self, prop_name))
                other_value = self.normalize(getattr(signup, prop_name))
                if value != other_value:
                    return False
        return True

    @property
    def id(self):
        return self.key().id()

    @property
    def can_update(self):
        return self.status == CustomerSignupStatus.PENDING

    @property
    def city_customer(self):
        return self.parent()

    @property
    def city(self):
        return self.city_customer.city


class Contact(db.Model):
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    email = db.StringProperty()
    phone_number = db.StringProperty()

    @property
    def id(self):
        return self.key().id()

    @property
    def customer_key(self):
        return self.parent_key()

    @property
    def customer(self):
        return Customer.get(self.customer_key)

    @staticmethod
    def list(customer_key):
        return list(Contact.all().ancestor(customer_key).order('first_name'))

    @staticmethod
    def get_one(customer_key):
        return Contact.all().ancestor(customer_key).get()

    @staticmethod
    def get_by_contact_id(customer, contact_id):
        return Contact.get_by_id(contact_id, customer)

    @classmethod
    def create_key(cls, contact_id, customer_id):
        return db.Key.from_path(cls.kind(), contact_id, parent=Customer.create_key(customer_id))


class OsaSequenceBaseModel(db.Model):
    last_number = db.IntegerProperty(default=0)

    @property
    def year(self):
        return int(self.key().name())

    @classmethod
    def _next_number(cls, legal_entity):
        azzert(db.is_in_transaction())
        azzert(legal_entity)
        year = str(datetime.datetime.now().year)
        number = cls.get_by_key_name(year, parent=legal_entity)
        if not number:
            number = cls(key_name=year, parent=legal_entity)
        number.last_number += 1
        number.put()
        return number

    @classmethod
    def next(cls, legal_entity):
        number = cls._next_number(legal_entity)
        return u"OSA.%s.%s" % (number.year, number.last_number)


class OrderNumber(OsaSequenceBaseModel):
    pass


class InvoiceNumber(OsaSequenceBaseModel):

    @classmethod
    def next(cls, legal_entity):
        number = cls._next_number(legal_entity)
        return str(number.year)[-2:] + str(number.last_number).rjust(6, '0')


class ChargeNumber(OsaSequenceBaseModel):

    @classmethod
    def next(cls, legal_entity):
        number = cls._next_number(legal_entity)
        return number.last_number


class Order(db.Model):
    STATUS_UNSIGNED = 0
    STATUS_SIGNED = 1
    STATUS_CANCELED = 2

    CUSTOMER_STORE_ORDER_NUMBER = '-1'

    date = db.IntegerProperty()
    amount = db.IntegerProperty()  # In euro cents
    vat_pct = db.IntegerProperty()
    vat = db.IntegerProperty()  # In euro cents
    total_amount = db.IntegerProperty()  # In euro cents
    contact_id = db.IntegerProperty()
    manager = db.UserProperty()

    signature = db.BlobProperty()
    pdf = db.BlobProperty()
    status = db.IntegerProperty(default=STATUS_UNSIGNED)
    is_subscription_order = db.BooleanProperty()
    is_subscription_extension_order = db.BooleanProperty(default=False)
    date_signed = db.IntegerProperty()
    next_charge_date = db.IntegerProperty()
    date_canceled = db.IntegerProperty()
    team_id = db.IntegerProperty()
    charge_interval = db.IntegerProperty(default=1)

    @property
    def id(self):
        return self.key().id()

    @property
    def order_number(self):
        return self.key().id_or_name()

    @property
    def amount_in_euro(self):
        return u'{:20,.2f}'.format(self.amount / 100.0)

    @property
    def vat_in_euro(self):
        return u'{:20,.2f}'.format(self.vat / 100.0)

    @property
    def total_amount_in_euro(self):
        return u'{:20,.2f}'.format(self.total_amount / 100.0)

    @property
    def full_date_str(self):
        return time.strftime(u'%d %b %Y %H:%M:%S', time.gmtime(self.date))

    @property
    def date_str(self):
        return time.strftime(u'%d/%m/%Y', time.gmtime(self.date))

    @property
    def customer_key(self):
        return self.parent_key()

    @property
    def customer_id(self):
        return self.parent_key().id()

    @classmethod
    def list(cls, customer_key):
        return list(cls.all().ancestor(customer_key).order('date'))

    @property
    def full_date_canceled_str(self):
        return time.strftime(u'%d %b %Y %H:%M:%S', time.gmtime(self.date_canceled))

    @property
    def contact_key(self):
        return db.Key.from_path(Contact.kind(), self.contact_id, parent=self.customer_key)

    @property
    def contact(self):
        return Contact.get_by_id(self.contact_id, self.customer_key)

    @property
    def signature_as_data_url(self):
        if not self.signature:
            return None
        return u"data:image/jpg;base64,%s" % base64.b64encode(self.signature)

    @staticmethod
    def get_by_order_number(customer_id, order_number):
        return db.get(Order.create_key(customer_id, order_number))

    @classmethod
    def create_key(cls, customer_id, order_number):
        return db.Key.from_path(cls.kind(), order_number, parent=Customer.create_key(customer_id))

    @staticmethod
    def list_unsigned(customer):
        return Order.all() \
            .ancestor(customer) \
            .filter('status', Order.STATUS_UNSIGNED) \
            .order('date')

    @staticmethod
    def list_signed(customer_key):
        return Order.all().ancestor(customer_key).filter('status', Order.STATUS_SIGNED).order('date')

    def list_items(self):
        order_item_qry = OrderItem.gql("WHERE ANCESTOR IS :ancestor ORDER BY number")
        order_item_qry.bind(ancestor=self)
        return list(order_item_qry)

    @classmethod
    def list_by_contact_id(cls, contact_id):
        return cls.all().filter('contact_id', contact_id)

    @staticmethod
    def default_next_charge_date():
        """Get the default next charge date (today + 1 month)."""
        next_month = datetime.datetime.utcfromtimestamp(now()) + relativedelta(months=1)
        return get_epoch_from_datetime(next_month)


class OrderItem(db.Expando):
    # Used for sorting
    number = db.IntegerProperty()
    product_code = db.StringProperty()
    count = db.IntegerProperty()
    comment = db.TextProperty()
    price = db.IntegerProperty()  # In euro cents

    # app_id : only for orderItems with product code NEWS
    # news_item_id: for orderItems with product code NEWS

    @property
    def price_in_euro(self):
        return '{:20,.2f}'.format(self.price / 100.0)

    @property
    def total_price_in_euro(self):
        return '{:20,.2f}'.format((self.price * self.count) / 100.0)

    def format_total_price(self, currency, locale=SHOP_DEFAULT_LANGUAGE, ratio=1.0, **kwargs):
        return format_currency(self.price * self.count * ratio / 100.0, currency, locale=locale, **kwargs)

    def format_price(self, currency, locale=SHOP_DEFAULT_LANGUAGE, ratio=1.0, **kwargs):
        return format_currency(self.price * ratio / 100.0, currency, locale=locale, **kwargs)

    @property
    def order_key(self):
        return self.parent_key()

    @property
    def order_number(self):
        return self.parent_key().name()

    @property
    def order(self):
        return Order.get(self.order_key)

    @property
    def clean_product_code(self):
        if "." not in self.product_code:
            return self.product_code
        return self.product_code.split(".", 1)[1]

    @property
    @db.non_transactional
    def product(self):
        return Product.get_by_key_name(self.product_code)

    @staticmethod
    def list_by_order(order_key):
        return OrderItem.all().ancestor(order_key)

    @classmethod
    def create_key(cls, customer_id, order_number, order_item_id):
        return db.Key.from_path(cls.kind(), order_item_id, parent=Order.create_key(customer_id, order_number))


class StripePaymentItem(NdbModel):
    product_code = ndb.StringProperty()
    count = ndb.IntegerProperty()


class StripePayment(NdbModel):
    STATUS_CREATED = 0
    STATUS_COMPLETED = 1

    create_date = ndb.DateTimeProperty(auto_now_add=True)
    service_user = ndb.UserProperty()

    status = ndb.IntegerProperty()
    items = ndb.LocalStructuredProperty(StripePaymentItem, repeated=True)

    @property
    def session_id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, session_id):
        return ndb.Key(cls, session_id)


class CreditCard(db.Model):  # todo remove deprecated
    creation_time = db.IntegerProperty()
    deleted = db.BooleanProperty(default=False)
    valid = db.BooleanProperty(default=True)
    contact_id = db.IntegerProperty()

    @property
    def stripe_card_id(self):
        return self.key().name()

    @property
    def customer_key(self):
        return self.parent_key()

    @property
    def customer(self):
        return Customer.get(self.customer_key)

    @property
    def contact(self):
        return Contact.get_by_id(self.contact_id, self.customer_key)

    @classmethod
    def list_by_contact_id(cls, contact_id):
        return cls.all().filter('contact_id', contact_id)


class StructuredInfoSequence(db.Model):
    last_number = db.IntegerProperty(default=0)

    @property
    def year(self):
        return int(self.key().name())

    @staticmethod
    def next():
        azzert(db.is_in_transaction())
        year = datetime.datetime.now().year
        sis = StructuredInfoSequence.get_by_key_name(str(year))
        if not sis:
            sis = StructuredInfoSequence(key_name=str(year))
        sis.last_number += 1
        sis.put()
        modulo = sis.last_number % 97
        if modulo == 0:
            modulo = 97
        modulo = "%02d" % (modulo)
        number = "%010d" % sis.last_number
        azzert(len(number + modulo) == 12)
        return "+++%s/%s/%s%s+++" % (number[0:3], number[3:7], number[7:10], modulo)


class Charge(db.Model):
    STATUS_PENDING = 0
    STATUS_EXECUTED = 1
    STATUS_CANCELLED = 2
    TYPE_ORDER_DELIVERY = 1
    TYPE_RECURRING_SUBSCRIPTION = 2
    # For customers without credit card that still want to participate
    TYPE_SUBSCRIPTION_EXTENSION = 3

    date = db.IntegerProperty()
    date_executed = db.IntegerProperty()
    date_cancelled = db.IntegerProperty()
    type = db.IntegerProperty()
    charge_number = db.IntegerProperty(indexed=True)

    amount = db.IntegerProperty(indexed=False)  # In euro cents
    vat_pct = db.IntegerProperty(indexed=False)
    vat = db.IntegerProperty(indexed=False)  # In euro cents
    total_amount = db.IntegerProperty(indexed=False)  # In euro cents
    amount_paid_in_advance = db.IntegerProperty(indexed=False, default=0)  # In euro cents
    currency_code = db.StringProperty(indexed=False, default=u'EUR')
    paid = db.BooleanProperty(indexed=False, default=False)

    status = db.IntegerProperty(default=0)

    log = db.TextProperty()

    structured_info = db.StringProperty(indexed=True)
    last_notification = db.IntegerProperty(indexed=False)
    payment_reminders = db.IntegerProperty(default=0, indexed=False)
    manager = db.UserProperty()
    team_id = db.IntegerProperty(indexed=True)
    customer_po_number = db.StringProperty(indexed=False)
    invoice_number = db.StringProperty(default='', indexed=False)

    subscription_extension_order_item_keys = db.ListProperty(db.Key, indexed=False)
    subscription_extension_length = db.IntegerProperty(indexed=False, default=1)

    @property
    def id(self):
        return self.key().id()

    @property
    def payment_overdue(self):
        return now() - self.last_notification > 7 * 24 * 3600

    @property
    def order_number(self):
        return self.parent_key().name()

    @property
    def customer_key(self):
        return self.key().parent().parent()

    @property
    def customer_id(self):
        return self.customer_key.id()

    @classmethod
    def create_key(cls, charge_id, order_number, customer_id):
        azzert(isinstance(charge_id, (int, long)))
        return db.Key.from_path(cls.kind(), charge_id, parent=Order.create_key(customer_id, order_number))

    @property
    def full_date_str(self):
        return time.strftime('%d %b %Y %H:%M:%S', time.gmtime(self.date))

    @property
    def last_notification_date_str(self):
        if self.last_notification:
            return time.strftime('%d %b %Y %H:%M:%S', time.gmtime(self.last_notification))
        else:
            return ""

    @property
    def amount_paid_in_advance_formatted(self):
        return '{:20,.2f}'.format(self.amount_paid_in_advance / 100.0)

    @property
    def total_amount_formatted(self):
        return '{:20,.2f}'.format(self.total_amount / 100.0)

    @property
    def amount_in_euro(self):
        return '{:20,.2f}'.format(self.amount / 100.0)

    @property
    def vat_in_euro(self):
        return '{:20,.2f}'.format(self.vat / 100.0)

    @property
    def total_amount_in_euro(self):
        return '{:20,.2f}'.format(self.total_amount / 100.0)

    @property
    def reference(self):
        # place a " * " between after every 3rd digit
        return u" * ".join(chunks(str(self.charge_number), 3)) if self.charge_number else None

    @property
    def is_recurrent(self):
        return self.type in (self.TYPE_SUBSCRIPTION_EXTENSION, self.TYPE_RECURRING_SUBSCRIPTION)

    @classmethod
    def get_by_reference(cls, charge_reference, customer_or_key=None):
        charge_number = long(re.sub('\D', '', charge_reference))  # removing all non-digit characters
        qry = cls.all()
        if customer_or_key:
            qry.ancestor(customer_or_key)
        return qry.filter('charge_number', charge_number).get()

    @property
    def currency(self):
        return get_currency_symbol(self.currency_code, SHOP_DEFAULT_LANGUAGE)

    @property
    def is_reseller_charge(self):
        return self.customer_key.kind() == LegalEntity.kind()


class Invoice(db.Model):
    PAYMENT_STRIPE = 1
    PAYMENT_MANUAL = 2
    PAYMENT_MANUAL_AFTER = 3
    PAYMENT_ON_SITE = 4

    date = db.IntegerProperty()
    pdf = db.BlobProperty()
    amount = db.IntegerProperty()  # In euro cents
    vat_pct = db.IntegerProperty()
    vat = db.IntegerProperty()  # In euro cents
    total_amount = db.IntegerProperty()  # In euro cents
    currency_code = db.StringProperty(indexed=False, default=u'EUR')

    # Paid -> On bank account
    paid = db.BooleanProperty(default=False)
    paid_timestamp = db.IntegerProperty()
    payment_type = db.IntegerProperty(default=0)  # Does not mean it's already on our bank account
    payment_term = db.IntegerProperty()
    operator = db.UserProperty()  # RegioManager
    legal_entity_id = db.IntegerProperty()

    @property
    def payment_term_formatted(self):
        d = datetime.datetime.fromtimestamp(self.payment_term, tz=get_timezone('Europe/Brussels'))
        return format_date(d, format='full', locale='nl_BE')

    @property
    def invoice_number(self):
        return self.key().name()

    @property
    def charge_id(self):
        return self.parent_key().id()

    @property
    def charge(self):
        return self.parent()

    @property
    def charge_key(self):
        return self.parent_key()

    @property
    def order_number(self):
        return self.parent_key().parent().name()

    @property
    def order_key(self):
        return self.parent_key().parent()

    @property
    def customer_id(self):
        return self.parent_key().parent().parent().id()

    @property
    def full_date_str(self):
        return time.strftime('%d %b %Y %H:%M:%S', time.gmtime(self.date))

    @property
    def date_str(self):
        return time.strftime('%d/%m/%Y', time.gmtime(self.date))

    @staticmethod
    def get_by_invoice_number(customer_id, order_number, charge_id, invoice_number):
        return db.get(Invoice.create_key(customer_id, order_number, charge_id, invoice_number))

    @classmethod
    def create_key(cls, customer_id, order_number, charge_id, invoice_number):
        return db.Key.from_path(cls.kind(), invoice_number,
                                parent=Charge.create_key(charge_id, order_number, customer_id))


class AuditLog(db.Model):
    date = db.IntegerProperty()
    customer_id = db.IntegerProperty()
    user = db.UserProperty()
    message = db.StringProperty(indexed=False)
    variables = db.TextProperty()


class ShopLoyaltySlide(db.Model):
    timestamp = db.IntegerProperty()
    name = db.StringProperty(indexed=False)
    time = db.IntegerProperty(indexed=False)
    item = blobstore.BlobReferenceProperty()  # deprecated
    gcs_filename = db.StringProperty(indexed=False)
    content_type = db.StringProperty(indexed=False)
    has_apps = db.BooleanProperty(default=True)
    apps = db.StringListProperty(indexed=True)
    function_dependencies = db.IntegerProperty(indexed=False)
    deleted = db.BooleanProperty(default=False)

    @property
    def id(self):
        return self.key().id()

    @property
    def str_apps(self):
        r = json.dumps(self.apps)
        return r

    def item_url(self):
        if self.gcs_filename:
            k = blobstore.create_gs_key('/gs' + self.gcs_filename)
        else:
            k = self.item
        return unicode(images.get_serving_url(k, secure_url=True))

    def slide_url(self):
        from rogerthat.settings import get_server_settings
        server_settings = get_server_settings()
        if self.gcs_filename:
            return get_serving_url(self.gcs_filename)
        return unicode("%s/unauthenticated/loyalty/slide?%s" % (
        server_settings.baseUrl, urllib.urlencode(dict(slide_key=self.item.key()))))


class ShopLoyaltySlideNewOrder(db.Model):
    timestamp = db.IntegerProperty(indexed=False)
    time = db.IntegerProperty(indexed=False)
    item = blobstore.BlobReferenceProperty()  # deprecated
    gcs_filename = db.StringProperty(indexed=False)
    content_type = db.StringProperty(indexed=False)

    @property
    def app_id(self):
        return self.key().name()

    def item_url(self):
        if self.gcs_filename:
            k = blobstore.create_gs_key('/gs' + self.gcs_filename)
        else:
            k = self.item
        return unicode(images.get_serving_url(k, secure_url=True))

    def slide_url(self):
        from rogerthat.settings import get_server_settings
        server_settings = get_server_settings()
        if self.gcs_filename:
            return get_serving_url(self.gcs_filename)
        return unicode("%s/unauthenticated/loyalty/slide?%s" % (
        server_settings.baseUrl, urllib.urlencode(dict(slide_key=self.item.key()))))

    @classmethod
    def create_key(cls, app):
        return db.Key.from_path(cls.kind(), app)


class RegioManagerStatistic(db.Model):
    month_revenue = db.ListProperty(int, indexed=False)  # [month, revenue] e.g.: [201509, 150000]
    day_revenue = db.ListProperty(int, indexed=False)  # [day, revenue] e.g.: [20150918, 9000, 20150919, 1000]

    @property
    def manager(self):
        return self.key().name()

    @classmethod
    def create_key(cls, manager_mail):
        return db.Key.from_path(cls.kind(), manager_mail)


class LegalEntity(CachedModelMixIn, db.Model):
    name = db.StringProperty(indexed=False)
    address = db.PostalAddressProperty(indexed=False)
    postal_code = db.StringProperty(indexed=False)
    city = db.StringProperty(indexed=False)
    country_code = db.StringProperty(indexed=False)
    phone = db.PhoneNumberProperty(indexed=False)
    email = db.EmailProperty(indexed=False)
    vat_percent = db.RatingProperty(indexed=False)  # min 0, max 100
    vat_number = db.StringProperty(indexed=False)
    iban = db.StringProperty(indexed=False)
    bic = db.StringProperty(indexed=False)
    terms_of_use = db.TextProperty()
    is_mobicage = db.BooleanProperty(required=True, indexed=True)
    currency_code = db.StringProperty(indexed=False, default=u'EUR')
    customer_id = db.IntegerProperty(indexed=False)
    contact_id = db.IntegerProperty(indexed=False)
    revenue_percentage = db.IntegerProperty(default=50)  # Their cut in %

    @property
    def is_reseller(self):
        return not self.is_mobicage

    @property
    def id(self):
        return self.key().id()

    @property
    def currency(self):
        return get_currency_symbol(self.currency_code, SHOP_DEFAULT_LANGUAGE)

    @property
    def revenue_percent(self):
        return self.revenue_percentage / 100.

    def country(self, language):
        return Locale(language).territories[self.country_code]

    def invalidateCache(self):
        if self.is_mobicage:
            from shop.dal import get_mobicage_legal_entity
            invalidate_cache(get_mobicage_legal_entity)

    @classmethod
    def create_key(cls, legal_entity_id):
        return db.Key.from_path(cls.kind(), legal_entity_id)

    @classmethod
    def list_all(cls):
        return cls.all()

    @classmethod
    def list_non_mobicage(cls, keys_only=False):
        return list(cls.all(keys_only=keys_only).filter('is_mobicage', False))

    @classmethod
    def get_mobicage(cls):
        from shop.dal import get_mobicage_legal_entity
        return get_mobicage_legal_entity()  # this method is cached

    def get_or_create_customer(self):
        if self.customer_id:
            return Customer.get_by_id(self.customer_id)
        else:
            from shop.bizz import create_contact
            customer = Customer(creation_time=now(),
                                team_id=RegioManagerTeam.get_mobicage().id,
                                manager=None,
                                vat=self.vat_number,
                                name=u'Reseller: %s' % self.name,
                                normalized_name=Customer.normalize_name(u'Reseller: %s' % self.name),
                                address1=self.address,
                                address2=u'',
                                zip_code=self.postal_code,
                                city=self.city,
                                country=self.country_code,
                                language='en',
                                organization_type=OrganizationType.PROFIT)
            customer.put()
            contact = create_contact(customer, u'Reseller', self.name, self.email, self.phone)
            self.customer_id = customer.id
            self.contact_id = contact.id
            self.put()
            return customer

    @classmethod
    def list_billable(cls):
        return cls.all().filter('revenue_percentage <', 100)


@deserializer
def ds_legal_entity(stream):
    return ds_model(stream, LegalEntity)


@serializer
def s_legal_entity(stream, model):
    s_model(stream, model, LegalEntity)


register(LegalEntity, s_legal_entity, ds_legal_entity)


class LegalDocumentType(object):
    TERMS_AND_CONDITIONS = 'terms-and-conditions'


class LegalDocumentAcceptance(NdbModel):
    date = ndb.DateTimeProperty(auto_now=True, indexed=False)
    version = ndb.IntegerProperty()
    headers = ndb.JsonProperty()

    @classmethod
    def create_key(cls, parent_key, type):  # @ReservedAssignment
        # type: (ndb.Key, unicode) -> ndb.Key
        return ndb.Key(cls._get_kind(), type, parent=parent_key)


class ShopExternalLink(NdbModel):
    title = ndb.StringProperty()
    description = ndb.TextProperty()
    url = ndb.StringProperty()


class ShopExternalLinks(NdbModel):
    links = ndb.StructuredProperty(ShopExternalLink, repeated=True, indexed=False)

    @classmethod
    def create_key(cls):
        return ndb.Key(cls, 'default')
