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

import json
import re
import urllib

import logging
from babel import Locale
from google.appengine.api import users as gusers, images
from google.appengine.ext import db, blobstore, ndb

from mcfw.properties import azzert
from mcfw.utils import Enum
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.consts import DAY
from rogerthat.models import ServiceProfile
from rogerthat.models.common import NdbModel
from rogerthat.rpc import users
from rogerthat.utils import bizz_check
from shop.exceptions import CustomerNotFoundException
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


_vat_validators = {
    'BE': _normalize_vat_be,
    'NL': _normalize_vat_nl,
    'FR': _normalize_vat_fr,
    'ES': _normalize_vat_es
}


def normalize_vat(country, vat):
    bizz_check(country in _vat_validators, "VAT validation is not supported for country " + country)
    return _vat_validators[country](vat)


class RegioManager(NdbModel):
    """
    Note:
        Key is the email of this manager.
    """
    ACCESS_NO = "no"
    ACCESS_READ_ONLY = "read-only"
    ACCESS_FULL = "full"

    name = ndb.StringProperty()

    @property
    def user(self):
        return gusers.User(self.email)

    @property
    def email(self):
        return self.key.id()

    @classmethod
    def create_key(cls, email):
        return ndb.Key(cls, email)

    def has_access(self):
        return self.ACCESS_FULL


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
    organization_type = db.IntegerProperty(default=ServiceProfile.ORGANIZATION_TYPE_PROFIT)
    managed_organization_types = db.ListProperty(int, indexed=False)
    migration_job = db.StringProperty(indexed=False)
    default_app_id = db.StringProperty()  # TODO communities: remove after migration
    community_id = db.IntegerProperty()
    website = db.StringProperty()
    facebook_page = db.StringProperty()
    # when set to anything lower than the current date that isn't 0, the
    # service of the customer will be disabled over night.
    service_disabled_at = db.IntegerProperty(default=0)  # 0 = not disabled
    disabled_reason = db.StringProperty(indexed=False)
    disabled_reason_int = db.IntegerProperty(default=0)

    stripe_id = db.StringProperty()  # todo remove deprecated
    stripe_id_created = db.IntegerProperty(default=0)  # todo remove deprecated
    stripe_credit_card_id = db.StringProperty()  # todo remove deprecated

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
        SolutionModule.ASK_QUESTION
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
