# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import json
import logging
import os

import jinja2
import webapp2
from jinja2 import StrictUndefined

from babel import dates, Locale
from mcfw.rpc import serialize_complex_value
from rogerthat.bizz import channel
from rogerthat.bizz.registration import get_headers_for_consent
from rogerthat.bizz.session import set_service_identity
from rogerthat.consts import DEBUG, APPSCALE
from rogerthat.dal.app import get_apps_by_id, get_app_by_id
from rogerthat.dal.profile import get_service_profile
from rogerthat.dal.service import get_service_identity
from rogerthat.models import ServiceIdentity
from rogerthat.pages.legal import get_version_content, DOC_TERMS_SERVICE, get_current_document_version
from rogerthat.pages.login import SessionHandler
from rogerthat.rpc import users
from rogerthat.service.api import system
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils.channel import send_message_to_session
from rogerthat.utils.service import create_service_identity_user
from shop.bizz import get_organization_types, is_signup_enabled, update_customer_consents, \
    get_customer_consents
from shop.business.legal_entities import get_vat_pct
from shop.constants import LOGO_LANGUAGES
from shop.dal import get_customer, get_mobicage_legal_entity
from solution_server_settings import get_solution_server_settings
from solutions import translate, translations, COMMON_JS_KEYS
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import OrganizationType, SolutionModule
from solutions.common.bizz.budget import BUDGET_RATE
from solutions.common.bizz.cityapp import get_country_apps
from solutions.common.bizz.functionalities import get_functionalities
from solutions.common.bizz.loyalty import is_joyn_available, is_oca_loyalty_limited
from solutions.common.bizz.settings import SLN_LOGO_WIDTH, SLN_LOGO_HEIGHT
from solutions.common.consts import UNITS, UNIT_SYMBOLS, UNIT_PIECE, UNIT_LITER, UNIT_KG, UNIT_GRAM, UNIT_HOUR, \
    UNIT_MINUTE, ORDER_TYPE_SIMPLE, ORDER_TYPE_ADVANCED, UNIT_PLATTER, UNIT_SESSION, UNIT_PERSON, UNIT_DAY, CURRENCIES, \
    get_currency_name
from solutions.common.dal import get_solution_settings, get_restaurant_menu, get_solution_email_settings, \
    get_solution_settings_or_identity_settings
from solutions.common.dal.city_vouchers import get_city_vouchers_settings
from solutions.common.dal.cityapp import get_cityapp_profile, get_service_user_for_city
from solutions.common.models import SolutionQR, SolutionServiceConsent
from solutions.common.models.news import NewsSettingsTags
from solutions.common.models.properties import MenuItem
from solutions.common.to import SolutionEmailSettingsTO
from solutions.flex import SOLUTION_FLEX
from solutions.jinja_extensions import TranslateExtension

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), 'templates'),
                                    os.path.join(os.path.dirname(__file__), '..', 'common', 'templates')]),
    extensions=[TranslateExtension])


DEFAULT_JS_TEMPLATES = [
    'inbox_messages',
    'inbox_detail_messages',
    'holiday_addholiday',
    'holiday_holiday',
    'qanda_question_table',
    'qanda_question_modules',
    'qanda_question_detail',
    'hints_modal',
    'shop/shopping_cart',
    'shop/product',
    'settings/settings_branding',
    'settings/settings_branding_preview',
    'settings/app_user_roles',
    'settings/app_user_admins',
    'settings/app_user_add_roles',
    'settings/try_publish_changes',
    'settings/upload_image',
    'functionalities/functionality',
    'city_select',
    'budget_balance_warning',
]

VECTOR_MAPS = {
    'BE': 'flanders.json'
}

MODULES_JS_TEMPLATE_MAPPING = {
    SolutionModule.AGENDA: [
        'events_add',
        'events_add_dates',
        'events',
        'events_events',
        'events_settings',
        'events_calendar_settings',
        'events_guests_modal',
        'events_guests_table',
        'events_uitcalendar_settings'
    ],
    SolutionModule.APPOINTMENT: [
        'timeframe_template'
    ],
    SolutionModule.BILLING: [
        'billing_budget',
        'billing_manage_credit_card',
        'billing_view_invoice',
        'billing_settings_unsigned_orders_table',
        'billing_settings_orders_table',
        'billing_settings_invoices_table'
    ],
    SolutionModule.BROADCAST: [
        'addattachment',
        'broadcast_types',
        'broadcast_schedule',
        'broadcast_schedule_items',
        'broadcast_settings_list',
        'broadcast_rss_settings',
        'broadcast/broadcast_news',
        'broadcast/broadcast_news_overview',
        'broadcast/broadcast_news_preview',
        'broadcast/news_stats_row',
        'broadcast/news_app_check_list'
    ],
    SolutionModule.CITY_APP: [
        'services/service',
        'services/service_form',
        'services/modules_list',
        'services/service_search',
        'settings/app_settings'
    ],
    SolutionModule.CITY_VOUCHERS: [
        'city_vouchers/city_vouchers_list',
        'city_vouchers/city_vouchers_transactions',
        'city_vouchers/city_vouchers_qrcode_export_list',
        'city_vouchers/city_vouchers_export_list'
    ],
    SolutionModule.DISCUSSION_GROUPS: [
        'discussion_groups/discussion_groups_list',
        'discussion_groups/discussion_groups_put'
    ],
    SolutionModule.GROUP_PURCHASE: [
        'group_purchase',
        'group_purchase_subscriptions'
    ],
    SolutionModule.LOYALTY: [
        'loyalty_slides',
        'loyalty_slide_add',
        'loyalty_tablets',
        'loyalty_tablet_modal',
        'loyalty_scans',
        'loyalty_scans_redeem_stamps_modal',
        'loyalty_lottery_add_modal',
        'loyalty_customer_visits_detail_modal',
        'loyalty_customer_visits_detail',
        'loyalty_customer_visit',
        'loyalty_lottery_history',
        'loyalty_export',
        'voucher_export'
    ],
    SolutionModule.MENU: [
        'menu',
        'menu_additem',
        'menu_editdescription',
        'menu_edit_image',
        'menu_import'
    ],
    SolutionModule.ORDER: [
        'order',
        'order_list',
        'pause_orders_modal',
        'timeframe_template',
        'menu',
        'menu_import',
        'menu_additem',
        'menu_editdescription',
        'menu_edit_image',
        'payments',
        'payconiq_nl',
    ],
    SolutionModule.PHARMACY_ORDER: [
        'pharmacy_order',
        'pharmacy_order_list'
    ],
    SolutionModule.RESTAURANT_RESERVATION: [
        'reservation_addshift',
        'reservation_addtable',
        'reservation_broken_reservations',
        'reservation_delete_table_confirmation',
        'reservation_editreservation',
        'reservation_edittables',
        'reservation_no_shift_found',
        'reservation_shiftcontents',
        'reservation_tablecontents',
        'reservation_update_reservation_tables',
        'reservations'
    ],
    SolutionModule.REPAIR: [
        'repair_order'
    ],
    SolutionModule.SANDWICH_BAR: [
        'sandwiches_order_inbox_detail',
        'sandwiches_list_item',
        'transaction_modal',
    ],
    SolutionModule.STATIC_CONTENT: [
        'static_content/static_content_select_icon',
        'static_content/static_content'
    ],

    SolutionModule.HIDDEN_CITY_WIDE_LOTTERY: [
        'loyalty_lottery_add_modal',
        'loyalty_customer_visits_detail_modal',
        'loyalty_customer_visits_detail',
        'loyalty_customer_visit',
        'loyalty_lottery_history',
        'loyalty_slides',
        'loyalty_slide_add'
    ],
}


class FlexHomeHandler(webapp2.RequestHandler):

    def _get_location_templates(self, sln_settings):
        tmpl_params = {'language': sln_settings.main_language or DEFAULT_LANGUAGE,
                       'debug': DEBUG,
                       'appscale': APPSCALE,
                       'service_user_email': sln_settings.service_user}
        templates = {}
        templates_to_get = {'location'}
        for tmpl in templates_to_get:
            templates[tmpl] = JINJA_ENVIRONMENT.get_template(tmpl + '.html').render(tmpl_params)
        templates = json.dumps(templates)
        return templates

    def _get_templates(self, sln_settings):
        tmpl_params = {'language': sln_settings.main_language or DEFAULT_LANGUAGE,
                       'debug': DEBUG,
                       'appscale': APPSCALE,
                       'currency': sln_settings.currency,  # TBD: use currencies?
                       'service_user_email': sln_settings.service_user}
        templates = {}
        templates_to_get = set()
        for tmpl in DEFAULT_JS_TEMPLATES:
            templates_to_get.add(tmpl)
        for module in sln_settings.modules:
            for tmpl in MODULES_JS_TEMPLATE_MAPPING.get(module, []):
                templates_to_get.add(tmpl)
        for tmpl in templates_to_get:
            templates[tmpl] = JINJA_ENVIRONMENT.get_template(tmpl + '.html').render(tmpl_params)
        templates = json.dumps(templates)
        return templates

    def _get_qr_codes(self, sln_settings, service_identity):
        return SolutionQR.list_by_user(sln_settings.service_user, service_identity, sln_settings.solution)

    def _get_days(self, sln_settings):
        return [(k, v.capitalize()) for k, v in dates.get_day_names('wide', locale=sln_settings.main_language or DEFAULT_LANGUAGE).items()]

    def _get_months(self, sln_settings, width):
        return [v.capitalize() for _, v in dates.get_month_names(width, locale=sln_settings.main_language or DEFAULT_LANGUAGE).items()]

    def _get_day_str(self, sln_settings, day):
        return dates.get_day_names('wide', locale=sln_settings.main_language or DEFAULT_LANGUAGE)[day].capitalize()

    def _get_week_days(self, sln_settings):
        return [self._get_day_str(sln_settings, day) for day in [6, 0, 1, 2, 3, 4, 5]]

    def get(self):
        service_user = users.get_current_user()
        if not service_user:
            self.redirect("/ourcityapp")
            return
        sln_settings = get_solution_settings(service_user)
        if not sln_settings or sln_settings.solution != SOLUTION_FLEX:
            self.redirect("/ourcityapp")
            return
        session_ = users.get_current_session()
        all_translations = {key: translate(sln_settings.main_language, SOLUTION_COMMON, key) for key in
                            translations[SOLUTION_COMMON]['en']}
        for key in COMMON_JS_KEYS:
            all_translations[key] = translate(sln_settings.main_language, SOLUTION_COMMON, COMMON_JS_KEYS[key])
        if sln_settings.identities:
            if not session_.service_identity:
                jinja_template = JINJA_ENVIRONMENT.get_template('locations.html')
                params = {'language': sln_settings.main_language or DEFAULT_LANGUAGE,
                          'debug': DEBUG,
                          'appscale': APPSCALE,
                          'templates': self._get_location_templates(sln_settings),
                          'service_name': sln_settings.name,
                          'service_display_email': sln_settings.qualified_identifier or service_user.email().encode("utf-8"),
                          'service_user_email': service_user.email().encode("utf-8"),
                          'currency': sln_settings.currency,  # TBD: use currencies?
                          'translations': json.dumps(all_translations)
                          }
                channel.append_firebase_params(params)
                self.response.out.write(jinja_template.render(params))
                return
        elif session_.service_identity:
            session_ = set_service_identity(session_, None)

        must_check_tos = not session_.layout_only and not session_.shop
        if must_check_tos:
            lastest_tos_version = get_current_document_version(DOC_TERMS_SERVICE)
            if get_service_profile(service_user).tos_version != lastest_tos_version:
                self.redirect('/terms')
                return

        service_identity = session_.service_identity if session_.service_identity else ServiceIdentity.DEFAULT
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        customer = get_customer(service_user)
        solution_server_settings = get_solution_server_settings()
        jinja_template = JINJA_ENVIRONMENT.get_template('index.html')

        days = self._get_days(sln_settings)
        day_flags = [(pow(2, day_num), day_name) for day_num, day_name in days]
        months = self._get_months(sln_settings, 'wide')
        months_short = self._get_months(sln_settings, 'abbreviated')
        week_days = self._get_week_days(sln_settings)
        loyalty_version = self.request.get("loyalty")
        if customer:
            if service_identity != ServiceIdentity.DEFAULT:
                service_identity_user = create_service_identity_user(service_user, service_identity)
                si = get_service_identity(service_identity_user)
                city_app_id = si.app_id
                active_app_ids = si.sorted_app_ids
            else:
                city_app_id = customer.app_id
                active_app_ids = customer.sorted_app_ids
            default_app = get_app_by_id(city_app_id)
            is_demo_app = default_app.demo
        else:
            city_app_id = None
            is_demo_app = False
            logging.info('Getting app ids from service identity since no customer exists for user %s', service_user)
            service_identity_user = create_service_identity_user(service_user, service_identity)
            active_app_ids = get_service_identity(service_identity_user).sorted_app_ids

        available_apps = get_apps_by_id(active_app_ids)

        locale = Locale.parse(sln_settings.main_language)
        currencies = {currency: get_currency_name(locale, currency) for currency in CURRENCIES}
        locale = Locale.parse('en_GB')
        currency_symbols = {currency: locale.currency_symbols.get(currency, currency) for currency in CURRENCIES}
        consts = {
            'UNIT_PIECE': UNIT_PIECE,
            'UNIT_LITER': UNIT_LITER,
            'UNIT_KG': UNIT_KG,
            'UNIT_GRAM': UNIT_GRAM,
            'UNIT_HOUR': UNIT_HOUR,
            'UNIT_MINUTE': UNIT_MINUTE,
            'UNIT_DAY': UNIT_DAY,
            'UNIT_PERSON': UNIT_PERSON,
            'UNIT_SESSION': UNIT_SESSION,
            'UNIT_PLATTER': UNIT_PLATTER,
            'ORDER_TYPE_SIMPLE': ORDER_TYPE_SIMPLE,
            'ORDER_TYPE_ADVANCED': ORDER_TYPE_ADVANCED,
            'ORDER_ITEM_VISIBLE_IN_MENU': MenuItem.VISIBLE_IN_MENU,
            'ORDER_ITEM_VISIBLE_IN_ORDER': MenuItem.VISIBLE_IN_ORDER,
            'ORGANIZATION_TYPES': {
                'CITY': OrganizationType.CITY,
                'EMERGENCY': OrganizationType.EMERGENCY,
                'PROFIT': OrganizationType.PROFIT,
                'NON_PROFIT': OrganizationType.NON_PROFIT,
            },
            'MAP_FILE': VECTOR_MAPS.get(customer.country) if customer else None,
            'CITY_APPS': get_country_apps(customer.country) if customer else {},
            'BUDGET_RATE': BUDGET_RATE,
            'NEWS_TAGS': {
                'FREE_REGIONAL_NEWS': NewsSettingsTags.FREE_REGIONAL_NEWS
            },
            'CURRENCY_SYMBOLS': currency_symbols
        }
        if not customer:
            mobicage_legal_entity = get_mobicage_legal_entity()
            vat_pct = mobicage_legal_entity.vat_percent
            legal_entity_currency = mobicage_legal_entity.currency
            is_mobicage = True
        else:
            vat_pct = get_vat_pct(customer)
            is_mobicage = customer.team.legal_entity.is_mobicage
            legal_entity_currency = customer.team.legal_entity.currency

        country = customer and customer.country
        functionality_modules = functionality_info = None
        if city_app_id and is_signup_enabled(city_app_id):
            functionality_modules, functionality_info = map(json.dumps, get_functionalities(country,
                                                                                            sln_settings.main_language,
                                                                                            sln_settings.modules,
                                                                                            sln_settings.activated_modules,
                                                                                            active_app_ids))

        vouchers_settings = None
        if city_app_id and SolutionModule.CITY_VOUCHERS in sln_settings.modules:
            vouchers_settings = get_city_vouchers_settings(city_app_id)

        joyn_available = is_joyn_available(country, sln_settings.modules, active_app_ids)
        oca_loyalty_limited = is_oca_loyalty_limited(joyn_available, sln_settings)
        city_service_user = get_service_user_for_city(city_app_id)
        is_city = service_user == city_service_user
        city_app_profile = city_service_user and get_cityapp_profile(city_service_user)
        news_review_enabled = city_app_profile and city_app_profile.review_news

        organization_types = get_organization_types(customer, sln_settings.main_language)
        params = {'stripePublicKey': solution_server_settings.stripe_public_key,
                  'language': sln_settings.main_language or DEFAULT_LANGUAGE,
                  'country': country,
                  'logo_languages': LOGO_LANGUAGES,
                  'sln_settings': sln_settings,
                  'sln_i_settings': sln_i_settings,
                  'debug': DEBUG,
                  'appscale': APPSCALE,
                  'templates': self._get_templates(sln_settings),
                  'service_name': sln_i_settings.name,
                  'service_display_email': sln_i_settings.qualified_identifier or service_user.email().encode("utf-8"),
                  'service_user_email': service_user.email().encode("utf-8"),
                  'service_identity': service_identity,
                  'has_multiple_locations': True if sln_settings.identities else False,
                  'qr_codes': self._get_qr_codes(sln_settings, service_identity),
                  'SolutionModule': SolutionModule,
                  'news_enabled': True,
                  'days': days,
                  'day_flags': day_flags,
                  'months': months,
                  'months_short': months_short,
                  'week_days': week_days,
                  'customer': customer,
                  'loyalty': True if loyalty_version else False,
                  'oca_loyalty_limited': oca_loyalty_limited,
                  'joyn_supported': joyn_available,
                  'city_app_id': city_app_id,
                  'is_demo_app': is_demo_app,
                  'functionality_modules': functionality_modules,
                  'functionality_info': functionality_info,
                  'email_settings': json.dumps(serialize_complex_value(SolutionEmailSettingsTO.fromModel(get_solution_email_settings(), service_user), SolutionEmailSettingsTO, False)),
                  'currencies': currencies.items(),
                  'currency': sln_settings.currency,  # TBD: use currencies?
                  'is_layout_user': session_.layout_only if session_ else False,
                  'SLN_LOGO_WIDTH': SLN_LOGO_WIDTH,
                  'SLN_LOGO_HEIGHT': SLN_LOGO_HEIGHT,
                  'active_app_ids': active_app_ids,
                  'active_apps': json.dumps(active_app_ids),
                  'all_apps': json.dumps([dict(id=a.app_id, name=a.name) for a in available_apps]),
                  'UNITS': json.dumps(UNITS),
                  'UNIT_SYMBOLS': json.dumps(UNIT_SYMBOLS),
                  'CONSTS': consts,
                  'CONSTS_JSON': json.dumps(consts),
                  'COUNTRY': customer and customer.country or u'',
                  'modules': json.dumps(sln_settings.modules),
                  'provisioned_modules': json.dumps(sln_settings.provisioned_modules),
                  'VAT_PCT': vat_pct,
                  'IS_MOBICAGE_LEGAL_ENTITY': is_mobicage,
                  'LEGAL_ENTITY_CURRENCY': legal_entity_currency,
                  'translations': json.dumps(all_translations),
                  'organization_types': organization_types,
                  'organization_types_json': json.dumps(dict(organization_types)),
                  'vouchers_settings': vouchers_settings,
                  'show_email_checkboxes': customer is not None,
                  'service_consent': get_customer_consents(customer.user_email) if customer else None,
                  'is_city': is_city,
                  'news_review_enabled': news_review_enabled,
                  }

        if SolutionModule.BULK_INVITE in sln_settings.modules:
            params['bulk_invite_message'] = translate(sln_settings.main_language, SOLUTION_COMMON,
                                                      "settings-bulk-invite-message",
                                                      app_name=system.get_identity().app_names[0])

        params['menu'] = get_restaurant_menu(service_user) if SolutionModule.MENU in sln_settings.modules else None

        channel.append_firebase_params(params)
        self.response.out.write(jinja_template.render(params))


class FlexLogoutHandler(SessionHandler):

    def get(self):
        service_user = users.get_current_user()
        sln_settings = get_solution_settings(service_user)

        if not sln_settings or sln_settings.solution != SOLUTION_FLEX or not sln_settings.identities:
            self.stop_session()
            return self.redirect('/ourcityapp')

        session_ = users.get_current_session()
        if session_.service_identity:
            session_ = set_service_identity(session_, None)

        send_message_to_session(service_user, session_, u"solutions.common.locations.update", si=None)
        self.redirect('/ourcityapp')


class TermsAndConditionsHandler(SessionHandler):

    def get(self):
        service_user = users.get_current_user()
        if not service_user:
            self.redirect('/ourcityapp')
            return
        sln_settings = get_solution_settings(service_user)
        if not sln_settings:
            self.stop_session()
            return self.redirect('/ourcityapp')
        lang = sln_settings.main_language
        version = get_current_document_version(DOC_TERMS_SERVICE)
        params = {
            'tac': get_version_content(lang, DOC_TERMS_SERVICE, version),
            'tac_version': version,
            'language': lang,
            'show_email_checkboxes': get_customer(service_user) is not None,
        }
        jinja_template = JINJA_ENVIRONMENT.get_template('terms.html')
        self.response.out.write(jinja_template.render(params))

    def post(self):
        service_user = users.get_current_user()
        if not service_user:
            self.redirect('/ourcityapp')
            return
        sln_settings = get_solution_settings(service_user)
        if not sln_settings:
            self.stop_session()
            return self.redirect('/ourcityapp')
        version = long(self.request.get('version')) or get_current_document_version(DOC_TERMS_SERVICE)
        customer = get_customer(service_user)
        if customer:
            context = u'User terms'
            update_customer_consents(customer.user_email, {
                SolutionServiceConsent.TYPE_NEWSLETTER: self.request.get(
                    SolutionServiceConsent.TYPE_NEWSLETTER) == 'on',
                SolutionServiceConsent.TYPE_EMAIL_MARKETING: self.request.get(
                    SolutionServiceConsent.TYPE_EMAIL_MARKETING) == 'on'
            }, get_headers_for_consent(self.request), context)
        service_profile = get_service_profile(service_user)
        service_profile.tos_version = version
        service_profile.put()
        self.redirect('/')
