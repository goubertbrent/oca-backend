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
import logging

from google.appengine.api import urlfetch
from google.appengine.ext import db, ndb
from typing import Dict

from babel import Locale
from babel.dates import get_timezone
from mcfw.cache import invalidate_cache, CachedModelMixIn
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from mcfw.serialization import deserializer, ds_model, serializer, s_model, register
from rogerthat.consts import DEBUG
from rogerthat.dal import parent_key, parent_key_unsafe, parent_ndb_key
from rogerthat.models import ServiceIdentity
from rogerthat.models.common import NdbModel
from rogerthat.rpc import users
from rogerthat.utils.service import get_identity_from_service_identity_user, \
    get_service_user_from_service_identity_user
from solutions.common import SOLUTION_COMMON
from solutions.common.models.properties import SolutionUserProperty, MenuCategoriesProperty, \
    ActivatedModulesProperty, ActivatedModuleTO, MenuCategoryTO
from solutions.common.utils import create_service_identity_user_wo_default


class SolutionInboxMessage(db.Model):
    INBOX_NAME_UNREAD = u"unread"
    INBOX_NAME_STARRED = u"starred"
    INBOX_NAME_READ = u"read"
    INBOX_NAME_TRASH = u"trash"
    INBOX_NAME_DELETED = u"deleted"

    CATEGORY_APPOINTMENT = 'appointment'
    CATEGORY_ASK_QUESTION = 'ask_question'
    CATEGORY_BULK_INVITE = 'bulk_invite'
    CATEGORY_GROUP_PURCHASE = 'group_purchase'  # Not yet implemented
    CATEGORY_LOYALTY = 'loyalty'
    CATEGORY_ORDER = 'order'
    CATEGORY_PHARMACY_ORDER = 'pharmacy_order'
    CATEGORY_REPAIR = 'repair'
    CATEGORY_RESTAURANT_RESERVATION = 'restaurant_reservation'
    CATEGORY_SANDWICH_BAR = 'sandwich_bar'
    CATEGORY_AGENDA = 'agenda'
    CATEGORY_CUSTOMER_SIGNUP = 'registration'
    CATEGORY_OCA_INFO = 'oca_info'
    CATEGORY_CITY_MESSAGE = 'city_message'
    CATEGORY_NEWS_REVIEW = 'news_review'

    ICON_NAMES = {CATEGORY_APPOINTMENT: u'fa-calendar-plus-o',
                  CATEGORY_ASK_QUESTION: u'fa-comments-o',
                  CATEGORY_BULK_INVITE: u'fa-user-plus',
                  CATEGORY_GROUP_PURCHASE: u'fa-shopping-cart',
                  CATEGORY_LOYALTY: u'fa-credit-card',
                  CATEGORY_ORDER: u'fa-shopping-basket',
                  CATEGORY_PHARMACY_ORDER: u'fa-medkit',
                  CATEGORY_REPAIR: u'fa-wrench',
                  CATEGORY_RESTAURANT_RESERVATION: u'fa-cutlery',
                  CATEGORY_SANDWICH_BAR: u'hamburger',
                  CATEGORY_AGENDA: u'fa-book',
                  CATEGORY_CUSTOMER_SIGNUP: u'fa-sign-in',
                  CATEGORY_OCA_INFO: u'fa-info',
                  CATEGORY_CITY_MESSAGE: u'fa-newspaper-o',
                  CATEGORY_NEWS_REVIEW: u'fa-newspaper-o'}

    TOPICS = {CATEGORY_APPOINTMENT: u'appointment',
              CATEGORY_ASK_QUESTION: u'ask-question',
              CATEGORY_BULK_INVITE: u'settings-bulk-invite',
              CATEGORY_GROUP_PURCHASE: u'group-purchase',
              CATEGORY_LOYALTY: u'loyalty',
              CATEGORY_ORDER: u'order',
              CATEGORY_PHARMACY_ORDER: u'order',
              CATEGORY_REPAIR: u'repair',
              CATEGORY_RESTAURANT_RESERVATION: u'reserve',
              CATEGORY_SANDWICH_BAR: u'order-sandwich',
              CATEGORY_AGENDA: u'agenda',
              CATEGORY_CUSTOMER_SIGNUP: u'registration',
              CATEGORY_OCA_INFO: u'oca_info',
              CATEGORY_CITY_MESSAGE: u'city_message',
              CATEGORY_NEWS_REVIEW: u'news_review'}

    # for compatibility with older category names
    ICON_NAMES['customer_signup'] = ICON_NAMES[CATEGORY_CUSTOMER_SIGNUP]
    TOPICS['customer_signup'] = TOPICS[CATEGORY_CUSTOMER_SIGNUP]

    category = db.StringProperty(indexed=False)  # only filled in on parent message
    category_key = db.StringProperty(indexed=False)  # only filled in on parent message

    sent_by_service = db.BooleanProperty(indexed=False)
    sender = SolutionUserProperty()
    message_key = db.StringProperty(indexed=False)  # Rogerthat mk (for migrated models this can be None)
    parent_message_key = db.StringProperty()  # Rogerthat pmk
    message_key_by_tag = db.TextProperty()  # only filled in on parent message

    timestamp = db.IntegerProperty(indexed=False)
    last_timestamp = db.IntegerProperty(indexed=True)  # only filled in on parent message
    message = db.TextProperty()
    last_message = db.TextProperty()  # only filled in on parent message
    awaiting_first_message = db.BooleanProperty(indexed=False)  # only filled in on parent message

    picture_urls = db.StringListProperty(indexed=False)
    video_urls = db.StringListProperty(indexed=False)

    reply_enabled = db.BooleanProperty(indexed=False)  # only filled in on parent message
    read = db.BooleanProperty(indexed=True)  # only filled in on parent message
    starred = db.BooleanProperty(indexed=True)  # only filled in on parent message
    trashed = db.BooleanProperty(indexed=True)  # only filled in on parent message
    deleted = db.BooleanProperty(indexed=True)  # only filled in on parent message

    child_messages = db.ListProperty(int, indexed=False)  # only filled in on parent message

    @property
    def icon(self):
        if self.category and self.category in SolutionInboxMessage.ICON_NAMES:
            return SolutionInboxMessage.ICON_NAMES[self.category]
        elif self.category:
            logging.error("SolutionInboxMessage icon not found for category '%s' key '%s'", self.category, self.key())
        return None

    @property
    def icon_color(self):
        if self.category:
            return u"#000000"
        return None

    @property
    def chat_topic_key(self):
        if self.category and self.category in SolutionInboxMessage.TOPICS:
            return SolutionInboxMessage.TOPICS[self.category]
        elif self.category:
            logging.error(
                "SolutionInboxMessage chat_topic_key not found for category '%s' key '%s'", self.category, self.key())
        return None

    @property
    def id(self):
        return self.key().id()

    @property
    def service_identity_user(self):
        pkey = self.parent_key()
        if pkey.kind() == self.kind():
            return users.User(pkey.parent().name())
        return users.User(pkey.name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @property
    def solution_inbox_message_key(self):
        return str(self.key())

    def get_child_messages(self):
        if self.child_messages:
            return SolutionInboxMessage.get_by_id(self.child_messages, self)
        return []

    @classmethod
    def get_all_by_service(cls, service_user, service_identity, start_date):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        ancestor = parent_key_unsafe(service_identity_user, SOLUTION_COMMON)
        return cls.all().ancestor(ancestor) \
            .filter('parent_message_key', None) \
            .filter('deleted =', False) \
            .filter('last_timestamp >', start_date) \
            .order('-last_timestamp')

    @classmethod
    def create_key(cls, msg_id, parent):
        return db.Key.from_path(cls.kind(), msg_id, parent=parent)


class SolutionMessage(db.Model):
    message = db.TextProperty()
    parent_message_key = db.StringProperty(indexed=False)
    sender = SolutionUserProperty()
    timestamp = db.IntegerProperty(indexed=True)
    deleted = db.BooleanProperty(indexed=True, default=False)
    reply = db.TextProperty()
    reply_enabled = db.BooleanProperty(indexed=True, default=True)

    solution_inbox_message_key = db.StringProperty(indexed=False)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def solution_message_key(self):
        return str(self.key())


class SolutionIdentitySettings(db.Expando):
    name = db.StringProperty(indexed=False)  # TODO: remove usages and use ServiceInfo model instead
    # Inbox
    inbox_forwarders = db.StringListProperty(indexed=False)
    inbox_connector_qrcode = db.StringProperty(indexed=False)
    inbox_mail_forwarders = db.StringListProperty(indexed=False)
    inbox_email_reminders_enabled = db.BooleanProperty(indexed=False)

    broadcast_create_news_qrcode = db.StringProperty(indexed=False)

    payment_enabled = db.BooleanProperty(default=False)
    payment_optional = db.BooleanProperty(default=True)
    payment_test_mode = db.BooleanProperty(default=DEBUG)

    @staticmethod
    def create_key(service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return db.Key.from_path(SolutionIdentitySettings.kind(), service_identity_user.email(),
                                parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    def get_forwarders_by_type(self, forwarder_type):
        if forwarder_type == SolutionSettings.INBOX_FORWARDER_TYPE_MOBILE:
            return self.inbox_forwarders
        elif forwarder_type == SolutionSettings.INBOX_FORWARDER_TYPE_EMAIL:
            return self.inbox_mail_forwarders
        else:
            raise ValueError("Unexpected inbox forwarder type %s" % forwarder_type)


class SolutionSettings(SolutionIdentitySettings):
    INBOX_FORWARDER_TYPE_EMAIL = u'email'
    INBOX_FORWARDER_TYPE_MOBILE = u'mobile'

    login = db.UserProperty(indexed=False)
    identities = db.StringListProperty(indexed=False)

    iban = db.StringProperty(indexed=False)
    bic = db.StringProperty(indexed=False)

    search_enabled = db.BooleanProperty(indexed=False, default=False)

    # TODO: remove and use ServiceInfo instead
    currency = db.StringProperty(indexed=False)  # 3 letter symbol, e.g. EUR
    solution = db.StringProperty(indexed=False)
    timezone = db.StringProperty(indexed=False, default=u"Europe/Brussels")  # TODO: remove
    main_language = db.StringProperty(indexed=False)

    last_publish = db.IntegerProperty()
    updates_pending = db.BooleanProperty(indexed=False, default=False)
    update_date = db.DateTimeProperty(auto_now=True)
    auto_publish_date = db.DateTimeProperty()
    auto_publish_task_id = db.StringProperty()
    publish_changes_users = db.StringListProperty(indexed=False)
    provisioned_modules = db.StringListProperty()
    modules = db.StringListProperty()
    modules_to_put = db.StringListProperty(default=[])
    modules_to_remove = db.StringListProperty(default=[])
    activated_modules = ActivatedModulesProperty()
    activated_modules_json = db.TextProperty()

    # Events
    events_visible = db.BooleanProperty(indexed=False, default=True)
    default_calendar = db.IntegerProperty(indexed=False)
    uitdatabank_actor_id = db.StringProperty(indexed=True)

    facebook_page = db.StringProperty(indexed=False)
    facebook_name = db.StringProperty(indexed=False)
    facebook_action = db.StringProperty(indexed=False)

    twitter_username = db.StringProperty(indexed=False)

    # Branding
    loyalty_branding_hash = db.StringProperty(indexed=False)

    service_disabled = db.BooleanProperty(default=False)
    hidden_by_city = db.DateTimeProperty(default=None)

    _tmp_activated_modules = None

    @staticmethod
    def create_key(service_user):
        return db.Key.from_path(SolutionSettings.kind(), service_user.email(),
                                parent=parent_key(service_user, SOLUTION_COMMON))

    @property
    def service_identity_user(self):
        azzert(False, u"service_identity_user should not be called on SolutionSettings")

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_identity(self):
        azzert(False, u"service_identity should not be called on SolutionSettings")

    @property
    def locale(self):
        if self.main_language == 'en':
            return 'en_GB'
        elif self.main_language == 'nl':
            return 'nl_BE'
        return self.main_language

    def uses_inbox(self):
        from solutions.common.bizz import SolutionModule
        return any((m in self.modules for m in SolutionModule.INBOX_MODULES))

    def ciklo_vouchers_only(self):
        from solutions.common.bizz import SolutionModule
        return len(self.modules) == 1 and SolutionModule.CIRKLO_VOUCHERS in self.modules

    def can_edit_services(self, customer):
        from solutions.common.bizz import SolutionModule, OrganizationType
        if SolutionModule.CITY_APP not in self.modules:
            return False
        if not customer or customer.country == u"FR" or customer.organization_type != OrganizationType.CITY:
            return False
        return True

    @staticmethod
    def label(module):
        return ' '.join([x.capitalize() for x in module.split('_')])

    @property
    def modules_labels(self):
        return sorted([(k, SolutionSettings.label(k)) for k in self.modules])

    @property
    def tz_info(self):
        return get_timezone(self.timezone)

    @property
    def currency_symbol(self):
        return Locale.parse(self.main_language).currency_symbols.get(self.currency, self.currency)

    def get_activated_modules(self):
        # type: () -> Dict[str, ActivatedModuleTO]
        if self._tmp_activated_modules is None:
            data = json.loads(self.activated_modules_json) if self.activated_modules_json else {}
            result = {}
            if data:
                for module, value in data.iteritems():
                    result[module] = ActivatedModuleTO.from_dict(value)
            elif self.activated_modules:
                for module in self.activated_modules:
                    result[module.name] = module
            self._tmp_activated_modules = result
        return self._tmp_activated_modules

    def save_activated_modules(self, data):
        # type: (Dict[str, ActivatedModuleTO]) -> None
        result = {}
        for module, value in data.iteritems():
            result[module] = value.to_dict()
        self.activated_modules_json = json.dumps(result)
        self._tmp_activated_modules = data


class SolutionBrandingSettings(db.Model):
    DEFAULT_DARK_MENU_ITEM_COLOR = u'4D4D4D'
    DEFAULT_LIGHT_MENU_ITEM_COLOR = u'B2B2B2'
    DEFAULT_DARK_BACKGROUND_COLOR = u'141414'
    DEFAULT_LIGHT_BACKGROUND_COLOR = u'EBEBEB'
    DEFAULT_DARK_TEXT_COLOR = u'B2B2B2'
    DEFAULT_LIGHT_TEXT_COLOR = u'4D4D4D'
    color_scheme = db.StringProperty(indexed=False, default='light')
    background_color = db.StringProperty(indexed=False)
    text_color = db.StringProperty(indexed=False)
    menu_item_color = db.StringProperty(indexed=False)
    show_identity_name = db.BooleanProperty(indexed=False, default=True)
    show_avatar = db.BooleanProperty(indexed=False, default=True)
    modification_time = db.IntegerProperty(default=0)
    recommend_enabled = db.BooleanProperty(default=True, indexed=False)
    left_align_icons = db.BooleanProperty(default=True, indexed=False)
    logo_url = db.StringProperty(default=None, indexed=False)
    avatar_url = db.StringProperty(default=None, indexed=False)

    @classmethod
    def create_key(cls, service_user):
        return db.Key.from_path(cls.kind(), cls.kind(), parent=parent_key(service_user, SOLUTION_COMMON))

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def get_by_user(cls, service_user):
        return cls.get(cls.create_key(service_user))

    @classmethod
    def default_background_color(cls, color_scheme):
        return cls.DEFAULT_LIGHT_BACKGROUND_COLOR if color_scheme != 'dark' else cls.DEFAULT_DARK_BACKGROUND_COLOR

    @classmethod
    def default_text_color(cls, color_scheme):
        return cls.DEFAULT_LIGHT_TEXT_COLOR if color_scheme != 'dark' else cls.DEFAULT_DARK_TEXT_COLOR

    @classmethod
    def default_menu_item_color(cls, color_scheme):
        return cls.DEFAULT_LIGHT_MENU_ITEM_COLOR if color_scheme != 'dark' else cls.DEFAULT_DARK_MENU_ITEM_COLOR

    def _download(self, url):
        result = urlfetch.fetch(url)  # type: urlfetch._URLFetchResult
        if result.status_code == 200:
            return result.content
        else:
            logging.debug('%s: %s', result.status_code, result.content)
            raise Exception('Could not download %s' % url)

    def download_logo(self):
        return self._download(self.logo_url)

    def download_avatar(self):
        return self._download(self.avatar_url)


class SolutionMainBranding(db.Model):
    # key_name = user email
    blob = db.BlobProperty(indexed=False)

    # Do not set branding_key to None to force a system.store_branding, but set branding_creation_time to 0
    branding_key = db.StringProperty(indexed=False)  # Rogerthat branding key
    branding_creation_time = db.IntegerProperty(default=0)

    @property
    def service_user(self):
        return users.User(self.key().name())

    @staticmethod
    def create_key(service_user):
        return db.Key.from_path(SolutionMainBranding.kind(), service_user.email())


class RestaurantMenu(db.Model):
    categories = MenuCategoriesProperty()
    categories_json = db.TextProperty()
    predescription = db.TextProperty()
    postdescription = db.TextProperty()
    name = db.StringProperty(indexed=False)
    is_default = db.BooleanProperty(indexed=False, default=False)

    _tmp_categories = None

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    def create_key(service_user, solution):
        return db.Key.from_path(RestaurantMenu.kind(), 'menu', parent=parent_key(service_user, solution))

    def get_categories(self):
        if self._tmp_categories is None:
            data = json.loads(self.categories_json) if self.categories_json else {}
            result = {}
            if data:
                for id_, value in data.iteritems():
                    result[id_] = MenuCategoryTO.from_dict(value)
            elif self.categories:
                for c in self.categories:
                    if c.id:
                        result[c.id] = c
                    else:
                        result[c.name] = c
            self._tmp_categories = result
        return self._tmp_categories

    def save_categories(self, data):
        result = {}
        for key, value in data.iteritems():
            result[key] = value.to_dict()
        self.categories_json = json.dumps(result)
        self._tmp_categories = data


class RestaurantInvite(db.Model):
    STATUS_INVITED = 1
    STATUS_ACCEPTED = 2
    STATUS_REJECTED = 3

    epoch = db.FloatProperty(indexed=True)
    status = db.IntegerProperty(required=True, default=STATUS_INVITED)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def invitee(self):
        return self.key().name()

    @staticmethod
    @returns(db.Key)
    @arguments(service_user=users.User, service_identity=unicode, invitee=unicode, solution=unicode)
    def create_key(service_user, service_identity, invitee, solution):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return db.Key.from_path(RestaurantInvite.kind(), invitee, parent=parent_key_unsafe(service_identity_user, solution))


class SolutionQR(db.Model):
    description = db.StringProperty(indexed=False)
    image_url = db.StringProperty(indexed=False)

    @property
    def name(self):
        return self.key().name()

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @classmethod
    def create_key(cls, name, service_user, service_identity, solution):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return db.Key.from_path(cls.kind(), name, parent=parent_key_unsafe(service_identity_user, solution))

    @classmethod
    def get_by_name(cls, name, service_user, service_identity, solution):
        return cls.get(cls.create_key(name, service_user, service_identity, solution))

    @classmethod
    def list_by_user(cls, service_user, service_identity, solution):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return cls.all().ancestor(parent_key_unsafe(service_identity_user, solution))


class SolutionNewsPublisher(db.Model):

    timestamp = db.IntegerProperty(indexed=False)
    app_user = db.UserProperty(indexed=True)

    @staticmethod
    def createKey(app_user, service_user, solution):
        return db.Key.from_path(SolutionNewsPublisher.kind(),
                                app_user.email(),
                                parent=parent_key(service_user, solution))


class SolutionEmailSettings(CachedModelMixIn, db.Model):
    visible_in_inbox = db.ListProperty(users.User, indexed=False)

    def invalidateCache(self):
        from solutions.common.dal import get_solution_email_settings
        logging.info("SolutionEmailSettings removed from cache.")
        invalidate_cache(get_solution_email_settings)


@deserializer
def ds_solution_email_settings(stream):
    return ds_model(stream, SolutionEmailSettings)


@serializer
def s_solution_email_settings(stream, app):
    s_model(stream, app, SolutionEmailSettings)


register(SolutionEmailSettings, s_solution_email_settings, ds_solution_email_settings)


class FileBlob(db.Model):
    content = db.BlobProperty()
    service_user_email = db.StringProperty()


class SolutionRssLink(NdbModel):
    url = ndb.StringProperty()
    dry_runned = ndb.BooleanProperty(default=False)
    group_type = ndb.StringProperty(default=None, indexed=False)
    community_ids = ndb.IntegerProperty(repeated=True, indexed=False)
    notify = ndb.BooleanProperty(default=True, indexed=False)


class SolutionRssScraperSettings(NdbModel):
    rss_links = ndb.LocalStructuredProperty(SolutionRssLink, repeated=True)  # type: list[SolutionRssLink]
    notify = ndb.BooleanProperty(default=True, indexed=False)  # TODO: remove after migration 008_rss_links

    @property
    def service_user_email(self):
        return self.key.parent().string_id().decode('utf-8')

    @property
    def service_user(self):
        return users.User(self.service_user_email)

    @property
    def service_identity(self):
        return self.key.string_id().decode('utf-8')

    @classmethod
    def create_parent_key(cls, service_user):
        return ndb.Key(cls, service_user.email())

    @classmethod
    def create_key(cls, service_user, service_identity):
        if not service_identity:
            service_identity = ServiceIdentity.DEFAULT
        return ndb.Key(cls,
                       service_identity,
                       parent=cls.create_parent_key(service_user))


class SolutionRssScraperItem(NdbModel):
    timestamp = ndb.IntegerProperty(indexed=True)
    dry_run = ndb.BooleanProperty(indexed=True)
    news_id = ndb.IntegerProperty()
    hash = ndb.StringProperty()
    date = ndb.DateTimeProperty()
    rss_url = ndb.StringProperty()

    @classmethod
    def create_parent_key(cls, service_user, service_identity):
        return SolutionRssScraperSettings.create_key(service_user, service_identity)

    @classmethod
    def create_key(cls, service_user, service_identity, unique_identifier):
        return ndb.Key(cls,
                       unique_identifier,
                       parent=cls.create_parent_key(service_user, service_identity))

    @classmethod
    def list_after_date(cls, service_user, service_identity, date):
        # newest first
        return cls.query(ancestor=cls.create_parent_key(service_user, service_identity)) \
            .filter(cls.date > date) \
            .order(-cls.date)


class SolutionServiceConsent(NdbModel):
    TYPE_EMAIL_MARKETING = u'email_marketing'
    TYPE_NEWSLETTER = u'newsletter'
    TYPE_CITY_CONTACT = u'city_contact'  # Permission for city to have access to private info from services
    TYPE_CIRKLO_SHARE = u'cirklo_share'  # Permission to share login email to cirklo, so we can invite services to cirklo
    EMAIL_CONSENT_TYPES = [TYPE_EMAIL_MARKETING, TYPE_NEWSLETTER]
    TYPES = EMAIL_CONSENT_TYPES + [TYPE_CITY_CONTACT, TYPE_CIRKLO_SHARE]

    types = ndb.StringProperty(repeated=True, choices=TYPES)  # type: list[str]

    @property
    def email(self):
        return self.key.id().decode('utf-8')

    @classmethod
    def create_key(cls, email):
        return ndb.Key(cls, email)

    @staticmethod
    def consents(model):
        return {
            type_: (type_ in model.types if model else False) for type_ in SolutionServiceConsent.TYPES
        }


class SolutionServiceConsentHistory(NdbModel):

    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    consent_type = ndb.StringProperty()
    data = ndb.JsonProperty(compressed=True)


class SolutionModuleAppText(NdbModel):
    MENU_ITEM_LABEL = u'menu_item_label'
    FIRST_FLOW_MESSAGE = u'first_flow_message'

    texts = ndb.JsonProperty(indexed=False)

    @classmethod
    def create_key(cls, service_user, module_name):
        parent_key = parent_ndb_key(service_user, SOLUTION_COMMON)
        return ndb.Key(cls, module_name, parent=parent_key)

    @classmethod
    def get_text(cls, service_user, module_name, *text_types):
        app_text = cls.create_key(service_user, module_name).get()
        if not app_text:
            return [None] * len(text_types)
        return [app_text.texts.get(text_type) for text_type in text_types]
