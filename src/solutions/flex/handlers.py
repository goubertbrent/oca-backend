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
import os

import jinja2
import webapp2
from babel import dates, Locale
from jinja2 import StrictUndefined, Undefined

from mcfw.rpc import serialize_complex_value
from rogerthat.bizz import channel
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.communities.models import AppFeatures
from rogerthat.bizz.registration import get_headers_for_consent
from rogerthat.bizz.session import set_service_identity
from rogerthat.consts import DEBUG
from rogerthat.dal.profile import get_service_profile
from rogerthat.models import ServiceIdentity
from rogerthat.pages.legal import get_version_content, DOC_TERMS_SERVICE, get_current_document_version
from rogerthat.pages.login import SessionHandler
from rogerthat.rpc import users
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils.channel import send_message_to_session
from shop.bizz import get_organization_types, update_customer_consents
from shop.business.legal_entities import get_vat_pct
from shop.constants import LOGO_LANGUAGES
from shop.dal import get_customer
from solutions import translate, translations, COMMON_JS_KEYS
from solutions.common.bizz import OrganizationType, SolutionModule
from solutions.common.bizz.budget import BUDGET_RATE
from solutions.common.bizz.functionalities import get_functionalities
from solutions.common.bizz.settings import get_service_info
from solutions.common.consts import UNITS, UNIT_SYMBOLS, UNIT_PIECE, UNIT_LITER, UNIT_KG, UNIT_GRAM, UNIT_HOUR, \
    UNIT_MINUTE, ORDER_TYPE_SIMPLE, ORDER_TYPE_ADVANCED, UNIT_PLATTER, UNIT_SESSION, UNIT_PERSON, UNIT_DAY, CURRENCIES
from solutions.common.dal import get_solution_settings, get_restaurant_menu, get_solution_email_settings, \
    get_solution_settings_or_identity_settings
from solutions.common.models import SolutionQR, SolutionServiceConsent
from solutions.common.models.properties import MenuItemTO
from solutions.common.to import SolutionEmailSettingsTO
from solutions.flex import SOLUTION_FLEX
from solutions.jinja_extensions import TranslateExtension

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), 'templates'),
                                    os.path.join(os.path.dirname(__file__), '..', 'common', 'templates')]),
    extensions=[TranslateExtension],
    undefined=StrictUndefined if DEBUG else Undefined)


DEFAULT_JS_TEMPLATES = [
    'inbox_messages',
    'inbox_detail_messages',
    'inbox_send_message_to_services',
    'qanda_question_table',
    'qanda_question_modules',
    'qanda_question_detail',
    'shop/shopping_cart',
    'shop/product',
    'settings/settings_branding',
    'settings/settings_branding_preview',
    'settings/app_user_roles',
    'settings/app_user_admins',
    'settings/app_user_add_roles',
    'settings/try_publish_changes',
    'functionalities/functionality',
    'budget_balance_warning',
]

MODULES_JS_TEMPLATE_MAPPING = {
    SolutionModule.AGENDA: [
        'events_add',
        'events_add_dates',
        'events',
        'events_events',
        'events_settings',
        'events_calendar_settings',
        'events_uitcalendar_settings'
    ],
    SolutionModule.APPOINTMENT: [
        'timeframe_template'
    ],
    SolutionModule.BILLING: [
        'billing_budget',
        'billing_view_invoice',
        'billing_settings_unsigned_orders_table',
        'billing_settings_orders_table',
        'billing_settings_invoices_table'
    ],
    SolutionModule.CITY_APP: [
        'services/service',
        'services/service_form',
        'services/modules_list',
        'services/service_search',
        'services/service_export',
        'settings/app_settings',
        'settings/paddle'
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
        'loyalty_export'
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
        'sandwiches_list_item'
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

    def _get_location_templates(self, service_user, language):
        tmpl_params = {'language': language,
                       'debug': DEBUG,
                       'service_user_email': service_user}
        templates = {}
        templates_to_get = {'location'}
        for tmpl in templates_to_get:
            templates[tmpl] = JINJA_ENVIRONMENT.get_template(tmpl + '.html').render(tmpl_params)
        templates = json.dumps(templates)
        return templates

    def _get_templates(self, lang, currency, modules):
        # type: (str, str, list[str]) -> str
        tmpl_params = {
            'language': lang or DEFAULT_LANGUAGE,
            'debug': DEBUG,
            'currency': currency,
        }
        templates = {}
        templates_to_get = set(DEFAULT_JS_TEMPLATES)
        for module in modules:
            for tmpl in MODULES_JS_TEMPLATE_MAPPING.get(module, []):
                templates_to_get.add(tmpl)
        for tmpl in templates_to_get:
            templates[tmpl] = JINJA_ENVIRONMENT.get_template(tmpl + '.html').render(tmpl_params)
        templates = json.dumps(templates)
        return templates

    def _get_qr_codes(self, sln_settings, service_identity):
        if SolutionModule.QR_CODES in sln_settings.modules:
            return SolutionQR.list_by_user(sln_settings.service_user, service_identity, sln_settings.solution)
        else:
            return []

    def _get_days(self, language):
        return [(k, v.capitalize()) for k, v in dates.get_day_names('wide', locale=language).items()]

    def _get_months(self, language, width):
        return [v.capitalize() for _, v in dates.get_month_names(width, locale=language).items()]

    def _get_day_str(self, language, day):
        return dates.get_day_names('wide', locale=language)[day].capitalize()

    def _get_week_days(self, language):
        return [self._get_day_str(language, day) for day in [6, 0, 1, 2, 3, 4, 5]]

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
        lang = sln_settings.main_language or DEFAULT_LANGUAGE
        all_translations = {key: translate(lang, key) for key in translations[DEFAULT_LANGUAGE]}
        for other_key, key in COMMON_JS_KEYS.iteritems():
            all_translations[other_key] = all_translations[key]
        service_identity = session_.service_identity if session_.service_identity else ServiceIdentity.DEFAULT
        service_info = get_service_info(service_user, service_identity)
        if sln_settings.identities:
            if not session_.service_identity:
                jinja_template = JINJA_ENVIRONMENT.get_template('locations.html')
                params = {
                    'language': lang,
                    'debug': DEBUG,
                    'templates': self._get_location_templates(service_user, lang),
                    'service_name': service_info.name,
                    'service_user_email': service_user.email().encode("utf-8"),
                    'currency': service_info.currency,
                    'translations': json.dumps(all_translations)
                }
                channel.append_firebase_params(params)
                self.response.out.write(jinja_template.render(params))
                return
        elif session_.service_identity:
            session_ = set_service_identity(session_, None)

        # Dont require terms of use for:
        # - shop users (admins)
        # - cities logging in on other services their dashboard (layout_only)
        # - cirklo-only customers
        must_check_tos = not session_.layout_only and not session_.shop and not sln_settings.ciklo_vouchers_only()
        service_profile = get_service_profile(service_user)
        if must_check_tos:
            lastest_tos_version = get_current_document_version(DOC_TERMS_SERVICE)
            if service_profile.tos_version != lastest_tos_version:
                self.redirect('/terms')
                return

        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        customer = get_customer(service_user)
        jinja_template = JINJA_ENVIRONMENT.get_template('index.html')

        days = self._get_days(lang)
        day_flags = [(pow(2, day_num), day_name) for day_num, day_name in days]
        months = self._get_months(lang, 'wide')
        months_short = self._get_months(lang, 'abbreviated')
        week_days = self._get_week_days(lang)
        loyalty_version = self.request.get("loyalty")

        community = get_community(service_profile.community_id)

        locale = Locale.parse(lang)
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
            'ORDER_ITEM_VISIBLE_IN_MENU': MenuItemTO.VISIBLE_IN_MENU,
            'ORDER_ITEM_VISIBLE_IN_ORDER': MenuItemTO.VISIBLE_IN_ORDER,
            'ORGANIZATION_TYPES': {
                'CITY': OrganizationType.CITY,
                'EMERGENCY': OrganizationType.EMERGENCY,
                'PROFIT': OrganizationType.PROFIT,
                'NON_PROFIT': OrganizationType.NON_PROFIT,
            },
            'BUDGET_RATE': BUDGET_RATE,
            'CURRENCY_SYMBOLS': currency_symbols
        }
        vat_pct = get_vat_pct(customer)
        is_mobicage = customer.team.legal_entity.is_mobicage
        legal_entity_currency = customer.team.legal_entity.currency

        functionality_modules = functionality_info = None
        if community.signup_enabled:
            functionality_modules, functionality_info = map(json.dumps, get_functionalities(
                lang, sln_settings.modules, sln_settings.activated_modules, community))

        is_city = service_user == community.main_service_user
        news_review_enabled = AppFeatures.NEWS_REVIEW in community.features

        default_router_location = u'#/functionalities'
        if sln_settings.ciklo_vouchers_only():
            default_router_location = u'#/vouchers'
        elif not functionality_modules:
            default_router_location = u'#/news'

        organization_types = get_organization_types(customer, community.default_app, lang, include_all=True)
        currency = service_info.currency
        params = {'language': lang,
                  'logo_languages': LOGO_LANGUAGES,
                  'sln_settings': sln_settings,
                  'sln_i_settings': sln_i_settings,
                  'hidden_by_city': sln_settings.hidden_by_city,
                  'debug': DEBUG,
                  'templates': self._get_templates(lang, currency, sln_settings.modules),
                  'service_name': service_info.name,
                  'service_user_email': service_user.email().encode("utf-8"),
                  'service_identity': service_identity,
                  'has_multiple_locations': True if sln_settings.identities else False,
                  'qr_codes': self._get_qr_codes(sln_settings, service_identity),
                  'SolutionModule': SolutionModule,
                  'days': days,
                  'day_flags': day_flags,
                  'months': months,
                  'months_short': months_short,
                  'week_days': week_days,
                  'customer': customer,
                  'loyalty': True if loyalty_version else False,
                  'functionality_modules': functionality_modules,
                  'functionality_info': functionality_info,
                  'email_settings': json.dumps(serialize_complex_value(
                      SolutionEmailSettingsTO.fromModel(get_solution_email_settings(), service_user),
                      SolutionEmailSettingsTO, False)),
                  'currency': currency,
                  'is_layout_user': session_.layout_only if session_ else False,
                  'UNITS': json.dumps(UNITS),
                  'UNIT_SYMBOLS': json.dumps(UNIT_SYMBOLS),
                  'CONSTS': consts,
                  'CONSTS_JSON': json.dumps(consts),
                  'modules': json.dumps(sln_settings.modules),
                  'provisioned_modules': json.dumps(sln_settings.provisioned_modules),
                  'VAT_PCT': vat_pct,
                  'IS_MOBICAGE_LEGAL_ENTITY': is_mobicage,
                  'LEGAL_ENTITY_CURRENCY': legal_entity_currency,
                  'translations': json.dumps(all_translations),
                  'organization_types': organization_types,
                  'organization_types_json': json.dumps(dict(organization_types)),
                  'is_city': is_city,
                  'news_review_enabled': news_review_enabled,
                  'can_edit_paddle': is_city and session_.shop,
                  'is_shop_admin': session_.shop if session_ else False,
                  'default_router_location': default_router_location
                  }

        if SolutionModule.BULK_INVITE in sln_settings.modules:
            params['bulk_invite_message'] = translate(lang, "settings-bulk-invite-message", app_name=community.name)

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
