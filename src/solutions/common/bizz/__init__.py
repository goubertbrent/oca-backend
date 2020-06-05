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
import os
import time
from collections import defaultdict
from datetime import datetime
from types import NoneType

import pytz
from PIL.Image import Image
from babel.dates import format_date, format_time, format_datetime, get_timezone
from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred, ndb
from google.appengine.ext.webapp import template
from typing import List

import solutions
from mcfw.cache import cached
from mcfw.consts import MISSING
from mcfw.properties import object_factory, unicode_property, long_list_property, bool_property, unicode_list_property, \
    azzert, long_property, typed_property
from mcfw.rpc import returns, arguments
from mcfw.utils import Enum
from rogerthat.bizz.branding import is_branding
from rogerthat.bizz.rtemail import generate_auto_login_url
from rogerthat.bizz.service import create_service, InvalidAppIdException, RoleNotFoundException, \
    AvatarImageNotSquareException
from rogerthat.consts import FAST_QUEUE, DEBUG
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.profile import get_service_profile
from rogerthat.dal.service import get_default_service_identity
from rogerthat.exceptions.branding import BrandingValidationException
from rogerthat.models import App, ServiceRole, Branding, OpeningHours, ServiceIdentity
from rogerthat.models.maps import MapServiceMediaItem
from rogerthat.models.news import MediaType
from rogerthat.models.settings import SyncedNameValue, ServiceInfo
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException, BusinessException
from rogerthat.rpc.users import User
from rogerthat.service.api import app, qr
from rogerthat.service.api.system import list_roles, add_role_member, delete_role_member, put_role, store_branding, \
    store_pdf_branding, put_reserved_menu_item_label
from rogerthat.to import TO
from rogerthat.to.app import AppInfoTO
from rogerthat.to.branding import BrandingTO
from rogerthat.to.friends import ServiceMenuDetailTO, ServiceMenuItemLinkTO
from rogerthat.to.messaging import BaseMemberTO
from rogerthat.to.messaging.flow import FormFlowStepTO, FLOW_STEP_MAPPING
from rogerthat.to.news import BaseMediaTO
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import generate_random_key, parse_color, channel, bizz_check, now, get_current_task_name, \
    try_or_defer
from rogerthat.utils.app import get_app_user_tuple
from rogerthat.utils.location import geo_code, GeoCodeStatusException, GeoCodeZeroResultsException
from rogerthat.utils.transactions import on_trans_committed
from solution_server_settings import get_solution_server_settings
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.consts import ORDER_TYPE_ADVANCED, OUR_CITY_APP_COLOUR, OCA_FILES_BUCKET
from solutions.common.dal import get_solution_settings, get_restaurant_menu
from solutions.common.dal.order import get_solution_order_settings
from solutions.common.exceptions import TranslatedException
from solutions.common.integrations.cirklo.models import VoucherSettings, VoucherProviderId
from solutions.common.models import SolutionSettings, SolutionMainBranding, \
    SolutionBrandingSettings, FileBlob, SolutionNewsPublisher, SolutionModuleAppText, RestaurantMenu
from solutions.common.models.order import SolutionOrderSettings, SolutionOrderWeekdayTimeframe
from solutions.common.to import ProvisionResponseTO
from solutions.flex import SOLUTION_FLEX

SERVICE_AUTOCONNECT_INVITE_TAG = u'service_autoconnect_invite_tag'


class OCAEmbeddedApps(Enum):
    # Contains shared functionality that is the same for many of the services
    # Including but not limitted to: q-matic appointments
    OCA = 'oca'


CITY_APP_BROADCAST_TYPES = [u'Trafic', u'Emergency']
ASSOCIATION_BROADCAST_TYPES = [u'News', u'Events']
MERCHANT_BROADCAST_TYPES = [u'Coupons', u'Daily specials', u'Info sessions'] + CITY_APP_BROADCAST_TYPES \
    + ASSOCIATION_BROADCAST_TYPES
DEFAULT_BROADCAST_TYPES = [item for item in MERCHANT_BROADCAST_TYPES if item not in CITY_APP_BROADCAST_TYPES]

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class SolutionModule(Enum):
    AGENDA = u'agenda'
    APPOINTMENT = u'appointment'
    ASK_QUESTION = u'ask_question'
    BILLING = u'billing'
    BROADCAST = u'broadcast'
    BULK_INVITE = u'bulk_invite'
    CITY_APP = u'city_app'
    CITY_VOUCHERS = u'city_vouchers'
    DISCUSSION_GROUPS = u'discussion_groups'
    GROUP_PURCHASE = u'group_purchase'
    LOYALTY = u'loyalty'
    MENU = u'menu'
    ORDER = u'order'
    PHARMACY_ORDER = u'pharmacy_order'
    QR_CODES = u'qr_codes'
    REPAIR = u'repair'
    RESTAURANT_RESERVATION = u'restaurant_reservation'
    SANDWICH_BAR = u'sandwich_bar'
    STATIC_CONTENT = u'static_content'
    WHEN_WHERE = u'when_where'
    JOBS = u'jobs'
    FORMS = u'forms'
    PARTICIPATION = u'participation'
    Q_MATIC = u'q_matic'
    REPORTS = u'reports'
    JCC_APPOINTMENTS = 'jcc_appointments'
    CIRKLO_VOUCHERS = 'cirklo_vouchers'

    HIDDEN_CITY_WIDE_LOTTERY = u'hidden_city_wide_lottery'

    MODULES_TRANSLATION_KEYS = {
        AGENDA: 'agenda',
        APPOINTMENT: 'appointment',
        ASK_QUESTION: 'ask-question',
        BILLING: 'Billing',
        BROADCAST: 'Broadcast',
        BULK_INVITE: 'settings-bulk-invite',
        DISCUSSION_GROUPS: 'discussion_groups',
        GROUP_PURCHASE: 'group-purchase',
        LOYALTY: 'loyalty',
        MENU: 'menu',
        ORDER: 'order',
        PHARMACY_ORDER: 'pharmacy_order',
        SANDWICH_BAR: 'order-sandwich',
        REPAIR: 'module_repair',
        RESTAURANT_RESERVATION: 'restaurant_reservation',
        STATIC_CONTENT: 'static-content',
        QR_CODES: 'settings-qr-codes',
        WHEN_WHERE: 'when-where',
        JOBS: 'jobs',
        FORMS: 'forms',
        PARTICIPATION: 'participation',
        REPORTS: 'oca.reports',
        JCC_APPOINTMENTS: 'jcc-appointments',
        CIRKLO_VOUCHERS: 'oca.cirklo_light',
    }

    INBOX_MODULES = (ASK_QUESTION, SANDWICH_BAR, APPOINTMENT, REPAIR, GROUP_PURCHASE, ORDER, RESTAURANT_RESERVATION,
                     PHARMACY_ORDER, CITY_APP)
    PROVISION_ORDER = defaultdict(lambda: 10, {BROADCAST: 20})  # Broadcast should be last for auto broadcast types

    # Modules allowed for static content subscriptions
    STATIC_MODULES = {WHEN_WHERE, BILLING, LOYALTY}
    # These are the modules that the customer or cityapp service of the customer can choose themselves
    ASSOCIATION_MODULES = {AGENDA, ASK_QUESTION, BROADCAST, BULK_INVITE, STATIC_CONTENT}
    POSSIBLE_MODULES = {AGENDA, APPOINTMENT, ASK_QUESTION, BROADCAST, BULK_INVITE, DISCUSSION_GROUPS, GROUP_PURCHASE,
                        LOYALTY, MENU, ORDER, PHARMACY_ORDER, REPAIR, RESTAURANT_RESERVATION, SANDWICH_BAR,
                        STATIC_CONTENT, FORMS, PARTICIPATION}
    MANDATORY_MODULES = {BILLING, QR_CODES, WHEN_WHERE}

    # order these in the order you want to show them in the apps
    SERVICE_ACTION_ORDER = {
        ORDER: 1,
        RESTAURANT_RESERVATION: 2,
        SANDWICH_BAR: 3,
        APPOINTMENT: 4,
        PHARMACY_ORDER: 5,
    }

    FUNCTIONALITY_MODULES = {BROADCAST, LOYALTY, ORDER, SANDWICH_BAR, RESTAURANT_RESERVATION, MENU, AGENDA,
                             PHARMACY_ORDER, HIDDEN_CITY_WIDE_LOTTERY, ASK_QUESTION, REPAIR, DISCUSSION_GROUPS,
                             APPOINTMENT}

    @classmethod
    def all(cls):
        # Filter out non-str attributes
        return filter(lambda x: isinstance(x, (str, unicode)),
                      super(SolutionModule, cls).all())

    @classmethod
    def visible_modules(cls):
        return filter(lambda x: not x.startswith("hidden_"), cls.all())

    @classmethod
    def hidden_modules(cls):
        return filter(lambda x: x.startswith("hidden_"), cls.all())

    @staticmethod
    def label(module):
        # split on '_', capitalize each part
        return ' '.join([x.capitalize() for x in module.split('_')])

    @classmethod
    def shop_modules(cls):
        return sorted([(k, cls.label(k)) for k in cls.visible_modules()])

    @classmethod
    def get_translated_description(cls, language, key):
        return solutions.translate(language, SOLUTION_COMMON, cls.MODULES_TRANSLATION_KEYS[key])

    @classmethod
    def action_order(cls, module):
        return SolutionModule.SERVICE_ACTION_ORDER.get(module, 0)


class OrganizationType(Enum):
    UNSPECIFIED = -1
    NON_PROFIT = 1
    PROFIT = 2
    CITY = 3
    EMERGENCY = 4

    @classmethod
    def get_translation_keys(cls):
        return {
            cls.UNSPECIFIED: 'Services',
            cls.NON_PROFIT: 'Associations',
            cls.PROFIT: 'Merchants',
            cls.CITY: 'Community Services',
            cls.EMERGENCY: 'Care',
        }


class SolutionServiceMenuItem(TO):
    icon_name = unicode_property('1')
    icon_color = unicode_property('2')
    label = unicode_property('3')
    tag = unicode_property('4')
    screen_branding = unicode_property('5')
    static_flow = unicode_property('6')
    requires_wifi = bool_property('7')  # False
    run_in_background = bool_property('8')  # True
    roles = long_list_property('9')  # []
    is_broadcast_settings = bool_property('10')  # False
    broadcast_branding = unicode_property('11')  # None
    broadcast_types = unicode_list_property('12')
    coords = long_list_property('13')
    action = long_property('14')
    link = typed_property('15', ServiceMenuItemLinkTO)
    embedded_app = unicode_property('embedded_app')

    def __init__(self, icon_name, icon_color, label, tag, screen_branding=None, requires_wifi=False,
                 run_in_background=True, static_flow=None, roles=None, is_broadcast_settings=False,
                 broadcast_branding=None, broadcast_types=None, coords=None, action=0, link=None, embedded_app=None):
        self.icon_name = icon_name
        self.icon_color = icon_color
        self.label = label
        self.tag = tag
        self.screen_branding = screen_branding
        self.requires_wifi = requires_wifi
        self.run_in_background = run_in_background
        self.static_flow = static_flow
        self.roles = [] if roles is None else roles
        self.is_broadcast_settings = is_broadcast_settings
        self.broadcast_branding = broadcast_branding
        self.broadcast_types = [] if broadcast_types is None else broadcast_types
        self.coords = [] if coords is None else coords
        self.action = action
        self.link = link
        self.embedded_app = embedded_app

BASE_CODE = ServiceApiException.BASE_CODE_SOLUTIONS


class BrandingNotFoundException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self,
                                     BASE_CODE,
                                     'Branding could not be downloaded')


class InvalidMenuItemColorException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self,
                                     BASE_CODE + 1,
                                     'Invalid menu item color')


class InvalidAddressException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self,
                                     BASE_CODE + 2,
                                     'Invalid address')


class GoogleMapsException(ServiceApiException):

    def __init__(self, status):
        ServiceApiException.__init__(self,
                                     BASE_CODE + 3,
                                     'Google Maps API returned "%s"' % status)


class InvalidEventException(BusinessException):
    pass


@returns(unicode)
@arguments(language=unicode, dt=datetime)
def _format_date(language, dt):
    return format_date(dt, format='long', locale=language)


@returns(unicode)
@arguments(language=unicode, dt=datetime)
def _format_time(language, dt):
    return format_time(dt, format='short', locale=language)


@returns(unicode)
@arguments(language=unicode, dt=datetime)
def _format_weekday(language, dt):
    return format_date(dt, format='EEEE', locale=language)


@returns(unicode)
@arguments(service_user=users.User, key=unicode, solution=unicode)
def _translate(service_user, key, solution=SOLUTION_COMMON):
    settings = get_solution_settings(service_user)
    return common_translate(settings.main_language, solution, key)


@cached(1, request=True, memcache=False)
@returns(AppInfoTO)
@arguments(app_id=unicode)
def get_app_info_cached(app_id):
    return app.get_info(app_id)


def update_reserved_menu_item_labels(sln_settings):
    logging.warning(sln_settings.service_user)
    with users.set_user(sln_settings.service_user):
        for i, label in enumerate(['About', 'History', 'Call', 'Recommend']):
            put_reserved_menu_item_label(
                i, common_translate(sln_settings.main_language, SOLUTION_COMMON, label))


@returns(ProvisionResponseTO)
@arguments(solution=unicode, email=unicode, name=unicode, branding_url=unicode, menu_item_color=unicode,
           phone_number=unicode, languages=[unicode], currency=unicode, redeploy=bool,
           organization_type=int, modules=[unicode], broadcast_types=[unicode], apps=[unicode],
           owner_user_email=unicode, search_enabled=bool, broadcast_to_users=[users.User], websites=[SyncedNameValue],
           password=unicode, tos_version=(int, long, NoneType))
def create_or_update_solution_service(solution, email, name, branding_url, menu_item_color, phone_number,
                                      languages, currency, redeploy, organization_type=OrganizationType.PROFIT,
                                      modules=None, broadcast_types=None, apps=None, owner_user_email=None,
                                      search_enabled=False, broadcast_to_users=None, websites=None, password=None,
                                      tos_version=None):
    if not redeploy:
        password, sln_settings = \
            create_solution_service(email, name, branding_url, menu_item_color, phone_number,
                                    solution, languages, currency, organization_type=organization_type, modules=modules,
                                    broadcast_types=broadcast_types, apps=apps, owner_user_email=owner_user_email,
                                    search_enabled=search_enabled, websites=websites, password=password, tos_version=tos_version)
        service_user = sln_settings.service_user
    else:
        service_user = users.User(email)
        _, sln_settings = update_solution_service(service_user, branding_url, menu_item_color, solution, languages,
                                                  modules, broadcast_types, apps, organization_type)
        password = None

    # Slightly delay this as create_solution_service needs to run a task first to save the ServiceInfo
    deferred.defer(common_provision, service_user, broadcast_to_users=broadcast_to_users,
                   _transactional=db.is_in_transaction(), _queue=FAST_QUEUE, _countdown=2)

    resp = ProvisionResponseTO()
    resp.login = email
    resp.password = password
    resp.auto_login_url = generate_auto_login_url(service_user)
    return resp


@returns(tuple)
@arguments(service_user=users.User, branding_url=unicode, menu_item_color=unicode, solution=unicode,
           languages=[unicode], modules=[unicode], broadcast_types=[unicode], apps=[unicode], organization_type=int)
def update_solution_service(service_user, branding_url, menu_item_color, solution, languages, modules=None,
                            broadcast_types=None, apps=None, organization_type=None):
    if branding_url:
        resp = urlfetch.fetch(branding_url, deadline=60)
        if resp.status_code != 200:
            raise BrandingNotFoundException()

        if not is_branding(resp.content, Branding.TYPE_NORMAL):
            raise BrandingValidationException("Content of branding download could not be identified as a branding")

    def trans():
        service_profile = get_service_profile(service_user, False)
        bizz_check(service_profile, "Service %s does not exist" % service_user.email())
        bizz_check(not service_profile.solution or service_profile.solution == solution,
                   u"Cannot change solution from %s to %s" % (service_profile.solution, solution))
        service_profile.solution = solution

        default_si = None
        if apps is not None:
            azzert(apps)
            default_si = get_default_service_identity(service_user)
            default_si.appIds = apps
            default_si.defaultAppId = apps[0]
            default_si.put()

        if organization_type is not None:
            service_profile.organizationType = organization_type

        solution_settings = get_solution_settings(service_user)
        solution_settings_changed = False
        if not solution_settings:
            default_si = default_si or get_default_service_identity(service_user)
            solution_settings = SolutionSettings(key=SolutionSettings.create_key(service_user), name=default_si.name)
            solution_settings_changed = True

        if solution_settings.solution != solution:
            solution_settings.solution = solution
            solution_settings_changed = True

        language_updated = False
        if languages:
            language_updated = solution_settings.main_language != languages[0]
            service_profile.supportedLanguages = languages
            solution_settings.main_language = languages[0]
            solution_settings_changed = True

        if menu_item_color == u"branding":
            solution_settings.menu_item_color = None
            solution_settings_changed = True
        elif menu_item_color:
            try:
                parse_color(menu_item_color)
            except ValueError:
                raise InvalidMenuItemColorException()

            solution_settings.menu_item_color = menu_item_color
            solution_settings_changed = True

        if modules is not None:
            solution_settings.modules = modules
            solution_settings_changed = True

        if broadcast_types is not None:
            solution_settings.broadcast_types = broadcast_types
            solution_settings_changed = True

        main_branding, branding_settings = db.get([SolutionMainBranding.create_key(service_user),
                                                   SolutionBrandingSettings.create_key(service_user)])
        if not main_branding:
            main_branding = SolutionMainBranding(key=SolutionMainBranding.create_key(service_user))
            if not branding_url:
                main_branding.put()
        if branding_url:
            main_branding.blob = db.Blob(resp.content)
            main_branding.branding_creation_time = 0
            main_branding.put()

        if not branding_settings:
            branding_settings = _get_default_branding_settings(service_user)
            branding_settings.put()

        service_profile.put()
        if solution_settings_changed:
            solution_settings.put()
        return language_updated, solution_settings

    if db.is_in_transaction:
        return trans()
    else:
        xg_on = db.create_transaction_options(xg=True)
        return db.run_in_transaction_options(xg_on, trans)


@returns(tuple)
@arguments(email=unicode, name=unicode, branding_url=unicode, menu_item_color=unicode,
           phone_number=unicode, solution=unicode, languages=[unicode], currency=unicode, category_id=unicode,
           organization_type=int, fail_if_exists=bool, modules=[unicode], broadcast_types=[unicode], apps=[unicode],
           owner_user_email=unicode, search_enabled=bool, websites=[SyncedNameValue], password=unicode, tos_version=(int, long, NoneType))
def create_solution_service(email, name, branding_url=None, menu_item_color=None, phone_number=None,
                            solution=SOLUTION_FLEX, languages=None, currency=u"EUR", category_id=None,
                            organization_type=1,
                            fail_if_exists=True, modules=None, broadcast_types=None, apps=None, owner_user_email=None,
                            search_enabled=False, websites=None, password=None, tos_version=None):
    password = password or unicode(generate_random_key()[:8])
    if languages is None:
        languages = [DEFAULT_LANGUAGE]

    if menu_item_color == "branding":
        menu_item_color = None
    elif menu_item_color:
        try:
            parse_color(menu_item_color)
        except ValueError:
            raise InvalidMenuItemColorException()

    if branding_url:
        # Already download branding to validate url
        resp = urlfetch.fetch(branding_url, deadline=60)
        if resp.status_code != 200:
            raise BrandingNotFoundException()

        if not is_branding(resp.content, Branding.TYPE_NORMAL):
            raise BrandingValidationException("Content of branding download could not be identified as a branding")

    # Raises if service already existed
    create_service(email, name, password, languages, solution, category_id, organization_type, fail_if_exists,
                   supported_app_ids=apps, owner_user_email=owner_user_email, tos_version=tos_version)
    new_service_user = users.User(email)

    to_be_put = []

    settings = get_solution_settings(new_service_user)
    if not settings:
        settings = SolutionSettings(key=SolutionSettings.create_key(new_service_user),
                                    menu_item_color=menu_item_color,
                                    main_language=languages[0],
                                    solution=solution,
                                    search_enabled=search_enabled,
                                    modules=modules or [],
                                    broadcast_types=broadcast_types or [])
        service_info = ServiceInfo(key=ServiceInfo.create_key(new_service_user, ServiceIdentity.DEFAULT))
        service_info.visible = True
        service_info.name = name
        service_info.currency = currency
        service_info.timezone = settings.timezone
        service_info.cover_media = get_default_cover_media(organization_type)
        if phone_number:
            service_info.phone_numbers = [SyncedNameValue.from_value(phone_number)]
        if owner_user_email:
            service_info.email_addresses = [SyncedNameValue.from_value(owner_user_email)]
            if settings.uses_inbox():
                settings.inbox_email_reminders_enabled = True
                settings.inbox_mail_forwarders.append(owner_user_email)
        if websites:
            service_info.websites = websites

        settings.login = users.User(owner_user_email) if owner_user_email else None
        to_be_put.append(settings)
        if db.is_in_transaction():
            on_trans_committed(ndb.put_multi, [service_info])
        else:
            service_info.put()

    main_branding = SolutionMainBranding(key=SolutionMainBranding.create_key(new_service_user))
    to_be_put.append(main_branding)
    main_branding.branding_key = None
    if branding_url:
        main_branding.blob = db.Blob(resp.content)
    else:
        # Branding will be generated during provisioning
        to_be_put.append(_get_default_branding_settings(new_service_user))

    put_and_invalidate_cache(*to_be_put)

    deferred.defer(_after_service_created, new_service_user, _transactional=db.is_in_transaction(),
                   _queue=FAST_QUEUE)

    return password, settings


def _after_service_created(service_user):
    try_or_defer(service_auto_connect, service_user)
    try_or_defer(_execute_consent_actions, service_user)


def _execute_consent_actions(service_user):
    from shop.bizz import get_customer_consents
    from shop.dal import get_customer
    customer = get_customer(service_user)
    consents = get_customer_consents(customer.user_email)
    # If consent was given, automatically allow cirklo data to be shared instead of requiring city to toggle this
    if consents.TYPE_CIRKLO_SHARE in consents.types:
        settings = VoucherSettings(key=VoucherSettings.create_key(service_user))
        settings.customer_id = customer.id
        settings.app_id = customer.default_app_id
        settings.providers = [VoucherProviderId.CIRKLO]
        settings.put()


def get_default_cover_media(organization_type):
    # type: (int) -> List[MapServiceMediaItem]
    base_url = 'https://storage.googleapis.com/%s/image-library/logo/%s.jpg'
    mapping = {
        OrganizationType.CITY: 'community-service',
        OrganizationType.PROFIT: 'merchant',
        OrganizationType.UNSPECIFIED: 'merchant',
        OrganizationType.NON_PROFIT: 'association',
        OrganizationType.EMERGENCY: 'care',
    }
    url = base_url % (OCA_FILES_BUCKET, mapping[organization_type])
    media_item = MapServiceMediaItem()
    media_item.item = BaseMediaTO()
    media_item.item.type = MediaType.IMAGE
    media_item.item.content = url
    return [media_item]


def _get_default_branding_settings(service_user):
    return SolutionBrandingSettings(key=SolutionBrandingSettings.create_key(service_user),
                                    color_scheme='light',
                                    background_color=SolutionBrandingSettings.DEFAULT_LIGHT_BACKGROUND_COLOR,
                                    text_color=SolutionBrandingSettings.DEFAULT_LIGHT_TEXT_COLOR,
                                    menu_item_color=OUR_CITY_APP_COLOUR,
                                    show_identity_name=True,
                                    show_avatar=True,
                                    modification_time=now())


@returns(tuple)
@arguments(address=unicode)
def _get_location(address):
    try:
        result = geo_code(address)
    except GeoCodeStatusException as e:
        raise GoogleMapsException(e.message)
    except GeoCodeZeroResultsException as e:
        raise InvalidAddressException()

    location = result['geometry']['location']
    return location['lat'], location['lng']


@returns(unicode)
@arguments(language=unicode, file_name=unicode, template_dict=dict)
def render_common_content(language, file_name, template_dict):
    template_dict['language'] = language
    path = os.path.join(os.path.dirname(solutions.__file__), 'common', 'templates', file_name)
    return template.render(path, template_dict)


@returns(NoneType)
@arguments(sln_settings=SolutionSettings)
def broadcast_updates_pending(sln_settings):
    channel.send_message(sln_settings.service_user, 'solutions.common.settings.updates_pending',
                         updatesPending=sln_settings.updates_pending)


def validate_before_provision(service_user, sln_settings):
    # type: (users.User, SolutionSettings) -> List[str]
    from solutions.common.bizz.menu import menu_is_visible
    branding_settings = SolutionBrandingSettings.get_by_user(service_user)
    lang = sln_settings.main_language
    errors = []
    if not branding_settings.avatar_url:
        errors.append(common_translate(lang, SOLUTION_COMMON, 'default_settings_warning_avatar'))
    if not branding_settings.logo_url:
        errors.append(common_translate(lang, SOLUTION_COMMON, 'default_settings_warning_logo'))
    if menu_is_visible(sln_settings):
        menu = db.get(RestaurantMenu.create_key(service_user, sln_settings.solution))
        if not menu or menu.is_default:
            errors.append(
                common_translate(lang, SOLUTION_COMMON, 'default_settings_warning_menu'))
    identities = [ServiceIdentity.DEFAULT]
    keys = []
    if sln_settings.identities:
        identities.extend(sln_settings.identities)
    for identity in identities:
        keys.append(OpeningHours.create_key(service_user, identity))
        keys.append(ServiceInfo.create_key(service_user, identity))
    models = {model.key: model for model in ndb.get_multi(keys) if model}
    for identity in identities:
        hours = models.get(OpeningHours.create_key(service_user, identity))  # type: OpeningHours
        if not hours or hours.type not in (OpeningHours.TYPE_STRUCTURED, OpeningHours.TYPE_NOT_RELEVANT):
            errors.append(common_translate(lang, SOLUTION_COMMON, 'need_opening_hours_before_publish'))
        service_info = models.get(ServiceInfo.create_key(service_user, identity))  # type: ServiceInfo
        if not service_info or not service_info.place_types or not service_info.main_place_type:
            errors.append(common_translate(lang, SOLUTION_COMMON, 'need_place_type_before_publish'))
        if not service_info or not service_info.addresses:
            errors.append(common_translate(lang, SOLUTION_COMMON, 'configure_your_address'))
    return errors


def auto_publish(service_user):
    # type: (users.User) -> None
    logging.debug('Automatically publishing service %s', service_user.email())
    sln_settings = get_solution_settings(service_user)
    current_task_name = get_current_task_name()
    if sln_settings.auto_publish_task_id != current_task_name:
        logging.debug('Auto publish task id (%s) != current task name (%s), doing nothing.',
                      sln_settings.auto_publish_task_id, current_task_name)
    else:
        common_provision(service_user, run_checks=False)


@returns(NoneType)
@arguments(service_user=users.User, sln_settings=SolutionSettings, broadcast_to_users=[users.User],
           friends=[BaseMemberTO], run_checks=bool)
def common_provision(service_user, sln_settings=None, broadcast_to_users=None, friends=None, run_checks=False):
    from solutions.flex.bizz import provision

    try:
        start = time.time()
        settings_was_none = not bool(sln_settings)
        cur_user = users.get_current_user() or users.get_current_deferred_user()
        must_send_updates_to_flex = cur_user not in (None, MISSING) and (cur_user != service_user)

        last_publish = 0
        try:
            if not settings_was_none:
                azzert(db.is_in_transaction())
            else:
                sln_settings = get_solution_settings(service_user)

            if DEBUG or friends or not run_checks or is_demo_app(service_user):
                pass  # no check needed
            else:
                now_ = now()
                if sln_settings.last_publish and (sln_settings.last_publish + 15 * 60) > now_:
                    time_str = format_datetime(sln_settings.last_publish, 'HH:mm',
                                               tzinfo=get_timezone(sln_settings.timezone),
                                               locale=sln_settings.main_language)
                    raise BusinessException(common_translate(sln_settings.main_language,
                                                             SOLUTION_COMMON,
                                                             'you-can-only-publish-every-15-min',
                                                             time_str=time_str))
                last_publish = now_

            if run_checks:

                errors = validate_before_provision(service_user, sln_settings)
                if errors:
                    msg = common_translate(sln_settings.main_language, SOLUTION_COMMON,
                                           'default_settings_warning') + ':'
                    lines = [msg] + errors
                    raise BusinessException('\n • '.join(lines))
            needs_reload, sln_settings = provision(service_user, friends)
            if must_send_updates_to_flex or needs_reload:
                channel.send_message(cur_user, 'common.provision.success', needs_reload=needs_reload)
        except Exception as e:
            if not sln_settings:
                sln_settings = get_solution_settings(service_user)
            if must_send_updates_to_flex:
                if isinstance(e, BusinessException):
                    errormsg = e.message
                else:
                    errormsg = common_translate(sln_settings.main_language, SOLUTION_COMMON, 'failed_to_create_service')
                channel.send_message(cur_user, 'common.provision.failed',
                                     errormsg=errormsg)
            if broadcast_to_users:
                channel.send_message(broadcast_to_users, 'shop.provision.failed')
            raise

        def trans():
            if settings_was_none:
                settings = get_solution_settings(service_user)
            else:
                # sln_settings is not None when it is just created in the transaction started before calling this method
                settings = sln_settings

            if last_publish:
                settings.last_publish = last_publish
            settings.updates_pending = False
            settings.auto_publish_task_id = None
            settings.put()
            return settings

        if not friends:
            # set update pending to false
            if db.is_in_transaction():
                sln_settings = trans()
            else:
                sln_settings = db.run_in_transaction(trans)
            broadcast_updates_pending(sln_settings)

        logging.debug('Provisioning took %s seconds', time.time() - start)
    except (AvatarImageNotSquareException, TranslatedException, BusinessException):
        raise
    except Exception:
        logging.exception('Failure in common_provision', _suppress=False)

        if not sln_settings:
            sln_settings = get_solution_settings(service_user)
        raise BusinessException(
            common_translate(sln_settings.main_language, SOLUTION_COMMON, 'error-occured-unknown-try-again'))


@returns()
@arguments(service_user=users.User)
def service_auto_connect(service_user):
    from rogerthat.service.api.friends import invite as invite_api_call
    from rogerthat.bizz.friends import CanNotInviteFriendException

    solution_server_settings = get_solution_server_settings()
    with users.set_user(service_user):
        for invitee in solution_server_settings.solution_service_auto_connect_emails:
            try:
                invite_api_call(invitee, None, u"New Flex service created", DEFAULT_LANGUAGE, SERVICE_AUTOCONNECT_INVITE_TAG, None,
                                App.APP_ID_ROGERTHAT)
            except CanNotInviteFriendException:
                logging.debug('%s is already connected with %s', invitee, service_user)
            except InvalidAppIdException:
                logging.debug('%s is not supported for %s', App.APP_ID_ROGERTHAT, service_user)


@returns([unicode])
@arguments()
def get_all_existing_broadcast_types():
    # translate the keys and sort
    return sorted((common_translate(DEFAULT_LANGUAGE, SOLUTION_COMMON, k) for k in MERCHANT_BROADCAST_TYPES))


@returns(unicode)
@arguments(service_user=users.User, template_name=unicode)
def find_qr_template(service_user, template_name):
    logging.info("Searching '%s' QR template" % template_name)
    qr_template = None
    cursor = None
    while True:
        list_result = qr.list_templates(cursor)
        for tmpl in list_result.templates:
            if tmpl.description == template_name:
                qr_template = tmpl.id
                break
        else:
            if list_result.cursor:
                cursor = list_result.cursor
                continue
        # for loop did break or list_result has reached the end (list_result.cursor is None)
        break

    if not qr_template:
        logging.warning("Did not find '%s' QR template for service %s" % (template_name, service_user))

    return qr_template


@returns(int)
@arguments(timezone=unicode)
def timezone_offset(timezone):
    dt_now = datetime.now()
    tz = pytz.timezone(timezone)
    dt_sj = tz.localize(dt_now)
    return int((dt_sj - pytz.UTC.localize(dt_now)).total_seconds())


@arguments(step=FormFlowStepTO, name=unicode)
def _get_value(step, name):
    azzert(step.step_id == name)
    azzert(step.answer_id == u'positive')
    return step.form_result.result.value


@returns([int])
@arguments(service_menu=ServiceMenuDetailTO, smi_tag=unicode)
def get_coords_of_service_menu_item(service_menu, smi_tag):
    if smi_tag:
        for item in service_menu.items:
            if item.tag == smi_tag:
                return item.coords
    return None


@returns([int])
@arguments(all_taken_coords=list, preferred_page=int)
def get_next_free_spot_in_service_menu(all_taken_coords, preferred_page):
    return get_next_free_spots_in_service_menu(all_taken_coords, 1, preferred_page)[0]


@returns([list])
@arguments(all_taken_coords=[list], count=int, preferred_page=int)
def get_next_free_spots_in_service_menu(all_taken_coords, count=1, preferred_page=0):
    spots = list()
    spots_to_get = count
    start_x = 0

    if preferred_page == -1:
        # try with the first page at first
        z = 0
    else:
        z = preferred_page

    while True:
        if z == 0:
            start_y = 1
        else:
            start_y = 0
        for y in range(start_y, 3):
            for x in range(start_x, 4):
                if [x, y, z] not in all_taken_coords:
                    spots_to_get = spots_to_get - 1
                    spots.append([x, y, z])
                    if not spots_to_get > 0:
                        return spots
        z += 1


@arguments(steps=[object_factory("step_type", FLOW_STEP_MAPPING)], step_id=unicode)
def get_first_fmr_step_result_value(steps, step_id):
    for step in steps:
        if step.step_id == step_id:
            return step.get_value()
    return None


@returns(unicode)
@arguments(src=unicode, path=unicode, default_css=unicode)
def create_pdf(src, path, default_css=None):
    from xhtml2pdf import pisa
    """

    Args:
        src: The source to be parsed. This can be a file handle or a String - or even better - a Unicode object.
        path:The original file path or URL. This is needed to calculate relative paths of images and style sheets.

    Returns:
        unicode: String containing the PDF
    """
    orig_to_bytes = getattr(Image, "tobytes", None)
    if orig_to_bytes is None:
        Image.tobytes = Image.tostring
    output_stream = StringIO()
    pisa.CreatePDF(src=src, dest=output_stream, path=path, default_css=default_css)
    if orig_to_bytes is None:
        delattr(Image, 'tobytes')
    return output_stream.getvalue()


@returns(FileBlob)
@arguments(service_user=User, content=str)
def create_file_blob(service_user, content):
    image = FileBlob(content=db.Blob(content),
                     service_user_email=service_user.email())
    image.put()
    return image


@returns()
@arguments(service_user=User, file_id=long)
def delete_file_blob(service_user, file_id):
    file_to_delete = FileBlob.get_by_id(file_id)
    if file_to_delete:
        if file_to_delete.service_user_email != service_user.email():
            logging.warning(
                '%s tried to delete a file from %s!' % (service_user.email(), file_to_delete.service_user_email))
        else:
            file_to_delete.delete()
    else:
        logging.info('FileBlob with id %s has already been deleted' % file_id)


@returns(unicode)
@arguments(key=unicode, language=unicode)
def try_to_translate(key, language):
    try:
        return common_translate(language, SOLUTION_COMMON, key, suppress_warning=True)
    except:
        return key


@returns(dict)
@arguments(sln_settings=SolutionSettings)
def get_translated_broadcast_types(sln_settings):
    translated_broadcast_types = {}
    for bt in sln_settings.broadcast_types:
        bt_trans = try_to_translate(bt, sln_settings.main_language)
        translated_broadcast_types[bt_trans] = bt
    return translated_broadcast_types


@db.non_transactional
@returns(BrandingTO)
@arguments(description=unicode, content=unicode)
def put_branding(description, content):
    return store_branding(description, content)


@db.non_transactional
@returns(BrandingTO)
@arguments(description=unicode, content=unicode)
def put_pdf_branding(description, content):
    return store_pdf_branding(description, content)


@returns(int)
@arguments(role_name=unicode)
def get_role_id(role_name):
    roles = list_roles()
    for role in roles:
        if role.name == role_name:
            return role.id

    raise RoleNotFoundException(role_name)


@returns(BaseMemberTO)
@arguments(app_user=users.User)
def make_member_from_app_user(app_user):
    human_user, app_id = get_app_user_tuple(app_user)
    member = BaseMemberTO()
    member.member = human_user.email()
    member.app_id = app_id
    return member


@returns()
@arguments(app_user=users.User, role_name=unicode)
def assign_app_user_role(app_user, role_name):
    try:
        role_id = get_role_id(role_name)
    except RoleNotFoundException:
        logging.debug('Creating role "%s"', role_name)
        role_id = put_role(role_name, ServiceRole.TYPE_MANAGED)
    member = make_member_from_app_user(app_user)
    add_role_member(role_id, member)


@returns()
@arguments(app_user=users.User, role_name=unicode)
def revoke_app_user_role(app_user, role_name):
    role_id = get_role_id(role_name)
    member = make_member_from_app_user(app_user)
    delete_role_member(role_id, member)


@returns(SolutionNewsPublisher)
@arguments(app_user=users.User, service_user=users.User, solution=unicode)
def create_news_publisher(app_user, service_user, solution):
    """Create a news publisher and assign create news role."""
    from solutions.common.bizz.messaging import POKE_TAG_BROADCAST_CREATE_NEWS
    key = SolutionNewsPublisher.createKey(app_user, service_user, solution)
    publisher = db.get(key)
    if not publisher:
        publisher = SolutionNewsPublisher(key=key)
    publisher.app_user = app_user
    db.put(publisher)

    assign_app_user_role(app_user, POKE_TAG_BROADCAST_CREATE_NEWS)
    return publisher


def get_user_defined_roles():
    from solutions.common.bizz.messaging import POKE_TAG_BROADCAST_CREATE_NEWS

    user_defined_roles = [POKE_TAG_BROADCAST_CREATE_NEWS]
    return [role for role in list_roles() if role.name not in user_defined_roles]


@returns()
@arguments(app_user=users.User, service_user=users.User, solution=unicode)
def delete_news_publisher(app_user, service_user, solution):
    """Delete a news publisher and revoke create news role."""
    from solutions.common.bizz.messaging import POKE_TAG_BROADCAST_CREATE_NEWS
    key = SolutionNewsPublisher.createKey(app_user, service_user, solution)
    publisher = db.get(key)
    if publisher:
        db.delete(publisher)
        revoke_app_user_role(app_user, POKE_TAG_BROADCAST_CREATE_NEWS)


@returns()
@arguments(sln_settings=SolutionSettings, solution=unicode)
def set_default_broadcast_types(sln_settings, solution=SOLUTION_COMMON):
    if not sln_settings.broadcast_types:
        sln_settings.broadcast_types = []
        for broadcast_type in DEFAULT_BROADCAST_TYPES:
            translated = common_translate(sln_settings.main_language, solution, broadcast_type)
            sln_settings.broadcast_types.append(translated)


@returns(SolutionOrderSettings)
@arguments(sln_settings=SolutionSettings)
def set_advanced_order_settings(sln_settings):
    order_settings = get_solution_order_settings(sln_settings)
    order_settings.order_type = ORDER_TYPE_ADVANCED
    service_user = sln_settings.service_user
    menu = get_restaurant_menu(service_user)

    if not menu:
        from solutions.common.bizz.menu import _put_default_menu
        _put_default_menu(service_user)
    SolutionOrderWeekdayTimeframe.create_default_timeframes_if_nessecary(service_user, sln_settings.solution)

    return order_settings


@returns()
@arguments(sln_settings=SolutionSettings, module=unicode)
def activate_solution_module(sln_settings, module):
    modules_to_put = sln_settings.modules_to_put
    modules_to_remove = sln_settings.modules_to_remove

    if module not in modules_to_put:
        modules_to_put.append(module)
    if module in modules_to_remove:
        modules_to_remove.remove(module)


@returns()
@arguments(sln_settings=SolutionSettings, module=unicode)
def deactivate_solution_module(sln_settings, module):
    modules_to_put = sln_settings.modules_to_put
    modules_to_remove = sln_settings.modules_to_remove

    if module in modules_to_put:
        modules_to_put.remove(module)
    if module not in modules_to_remove:
        modules_to_remove.append(module)


@returns(tuple)
@arguments(service_user=users.User, module=unicode, enabled=bool, force=bool)
def validate_enable_or_disable_solution_module(service_user, module, enabled, force):
    if module not in SolutionModule.FUNCTIONALITY_MODULES:
        return False, None

    if not enabled or force:
        return True, None

    return True, None


@returns()
@arguments(service_user=users.User, module=unicode, enabled=bool)
def enable_or_disable_solution_module(service_user, module, enabled):
    sln_settings = get_solution_settings(service_user)
    # for broadcast module, it can be enabled only
    if module == SolutionModule.BROADCAST:
        if enabled:
            set_default_broadcast_types(sln_settings)
        else:
            return

    to_put = []
    if enabled:
        activate_solution_module(sln_settings, module)
        if module == SolutionModule.ORDER:
            order_settings = set_advanced_order_settings(sln_settings)
            if order_settings:
                to_put.append(order_settings)
        elif module == SolutionModule.HIDDEN_CITY_WIDE_LOTTERY:
            deactivate_solution_module(sln_settings, SolutionModule.LOYALTY)
        elif module == SolutionModule.LOYALTY:
            deactivate_solution_module(sln_settings, SolutionModule.HIDDEN_CITY_WIDE_LOTTERY)

        # don't enable loyalty if this is a city service
        if SolutionModule.CITY_APP in sln_settings.modules:
            if module == SolutionModule.LOYALTY:
                return
    else:
        deactivate_solution_module(sln_settings, module)

    # set customer has_loyalty if the module is loyalty
    if module == SolutionModule.LOYALTY:
        from shop.models import Customer
        customer = Customer.get_by_service_email(service_user.email())
        if customer:
            customer.has_loyalty = enabled
            to_put.append(customer)
    sln_settings.updates_pending = True
    to_put.append(sln_settings)
    put_and_invalidate_cache(*to_put)
    broadcast_updates_pending(sln_settings)


@cached(1, request=True, memcache=False)
@returns(unicode)
@arguments(service_user=users.User)
def get_default_app_id(service_user):
    si = get_default_service_identity(service_user)
    return si.defaultAppId


@cached(1, request=True, memcache=False)
@returns((int, long))
@arguments(service_user=users.User)
def get_organization_type(service_user):
    from shop.dal import get_customer
    customer = get_customer(service_user)
    if customer:
        return customer.organization_type
    return OrganizationType.UNSPECIFIED


def is_demo_app(service_user):
    return get_app_by_id(get_default_app_id(service_user)).demo


@returns()
@arguments(service_user=users.User, module_name=unicode, texts=dict)
def set_solution_module_app_text(service_user, module_name, texts):
    key = SolutionModuleAppText.create_key(service_user, module_name)
    app_text = key.get()
    if not app_text:
        app_text = SolutionModuleAppText(key=key)
    app_text.texts = texts
    app_text.put()
