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

import binascii
import datetime
import json
import logging
import os
import time
import urllib

from dateutil.relativedelta import relativedelta
from google.appengine.api import search, users as gusers
from google.appengine.ext import db
from google.appengine.ext.deferred import deferred
from google.appengine.ext.webapp import template
import webapp2

from mcfw.cache import cached
from mcfw.consts import MISSING
from mcfw.exceptions import HttpNotFoundException
from mcfw.restapi import rest, GenericRESTRequestHandler
from mcfw.rpc import serialize_complex_value, arguments, returns
from rogerthat.bizz.friends import user_code_by_hash, makeFriends, ORIGIN_USER_INVITE
from rogerthat.bizz.registration import get_headers_for_consent
from rogerthat.bizz.service import SERVICE_LOCATION_INDEX, re_index_map_only
from rogerthat.bizz.session import create_session
from rogerthat.dal.app import get_app_by_id
from rogerthat.exceptions.login import AlreadyUsedUrlException, InvalidUrlException, ExpiredUrlException
from rogerthat.models import ProfilePointer, ServiceProfile
from rogerthat.pages.legal import DOC_TERMS_SERVICE, get_current_document_version, get_version_content, \
    get_legal_language, LANGUAGES as LEGAL_LANGUAGES
from rogerthat.pages.login import SetPasswordHandler
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.settings import get_server_settings
from rogerthat.templates import get_languages_from_request
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS, WarningReturnStatusTO
from rogerthat.utils import get_epoch_from_datetime, bizz_check, try_or_defer
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.cookie import set_cookie
from rogerthat.utils.service import create_service_identity_user
from shop import SHOP_JINJA_ENVIRONMENT
from shop.bizz import create_customer_signup, complete_customer_signup, get_organization_types, \
    update_customer_consents, get_customer_signup, validate_customer_url_data, \
    get_customer_consents
from shop.business.i18n import shop_translate
from shop.business.permissions import is_admin
from shop.constants import OFFICIALLY_SUPPORTED_LANGUAGES
from shop.dal import get_all_signup_enabled_apps
from shop.models import Invoice, OrderItem, Product, Prospect, RegioManagerTeam, LegalEntity, Customer, \
    Quotation, CustomerSignup
from shop.to import CompanyTO, CustomerTO, CustomerLocationTO
from shop.view import get_shop_context, get_current_http_host
from solution_server_settings import get_solution_server_settings
from solutions import translate
from solutions.common.bizz.grecaptcha import recaptcha_verify
from solutions.common.bizz.settings import get_consents_for_app
from solutions.common.integrations.cirklo.cirklo import check_merchant_whitelisted
from solutions.common.integrations.cirklo.models import CirkloMerchant, CirkloCity
from solutions.common.models import SolutionServiceConsent
from solutions.common.restapi.services import do_create_service
from solutions.common.to.settings import PrivacySettingsGroupTO
from markdown import Markdown
from solutions.common.markdown_newtab import NewTabExtension

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO  # @UnusedImport


class ExportProductsHandler(webapp2.RequestHandler):

    def get(self):
        if self.request.headers.get('X-Rogerthat-Secret') != get_server_settings().secret:
            self.abort(401)

        products = export_products()

        self.response.headers['Content-Type'] = 'text/json'
        self.response.write(json.dumps(products))


class ExportInvoicesHandler(webapp2.RequestHandler):

    def get(self):
        if self.request.headers.get('X-Rogerthat-Secret') != get_server_settings().secret:
            self.abort(401)

        year = int(self.request.GET['year'])
        month = int(self.request.GET['month'])

        invoices = export_invoices(year, month)

        self.response.headers['Content-Type'] = 'text/json'
        self.response.write(json.dumps(invoices))


class ProspectCallbackHandler(webapp2.RequestHandler):

    def get(self):
        solution_server_settings = get_solution_server_settings()
        if not solution_server_settings.tropo_callback_token:
            logging.error("tropo_callback_token is not set yet")
            self.abort(401)

        if self.request.get('token') != solution_server_settings.tropo_callback_token:
            self.abort(401)

        prospect_id = self.request.get('prospect_id')
        if not prospect_id:
            logging.warn("missing prospect_id in prospect callback invite result")
            self.abort(401)

        status = self.request.get('status')
        if not status:
            logging.warn("missing status in prospect callback invite result")
            self.abort(401)

        if status not in Prospect.INVITE_RESULT_STRINGS:
            logging.warn("got unexpected status in prospect callback invite result %s", status)
            self.abort(401)

        prospect_interaction = db.get(prospect_id)
        if not prospect_interaction:
            logging.warn("could not find prospect with key %s", prospect_id)
            self.abort(401)

        prospect = prospect_interaction.prospect
        logging.info("Process callback invite result for prospect with id '%s' and status '%s'", prospect.id, status)
        if status == Prospect.INVITE_RESULT_STRING_YES:
            prospect_interaction.code = prospect.invite_code = Prospect.INVITE_CODE_ANSWERED
            prospect_interaction.result = prospect.invite_result = Prospect.INVITE_RESULT_YES
        elif status == Prospect.INVITE_RESULT_STRING_NO:
            prospect_interaction.code = prospect.invite_code = Prospect.INVITE_CODE_ANSWERED
            prospect_interaction.result = prospect.invite_result = Prospect.INVITE_RESULT_NO
        elif status == Prospect.INVITE_RESULT_STRING_MAYBE:
            prospect_interaction.code = prospect.invite_code = Prospect.INVITE_CODE_ANSWERED
            prospect_interaction.result = prospect.invite_result = Prospect.INVITE_RESULT_MAYBE
        elif status == Prospect.INVITE_RESULT_STRING_NO_ANSWER:
            prospect_interaction.code = prospect.invite_code = Prospect.INVITE_CODE_NO_ANSWER
        elif status == Prospect.INVITE_RESULT_STRING_CALL_FAILURE:
            prospect_interaction.code = prospect.invite_code = Prospect.INVITE_CODE_CALL_FAILURE

        db.put([prospect, prospect_interaction])
        self.response.out.write("Successfully processed invite result")


class StaticFileHandler(webapp2.RequestHandler):

    def get(self, filename):
        cur_path = os.path.dirname(__file__)
        path = os.path.join(cur_path, u'html', filename)
        with open(path, 'r') as f:
            self.response.write(f.read())


def model_to_dict(model):
    d = db.to_dict(model)
    if 'pdf' in d:
        del d['pdf']
    for k, v in d.iteritems():
        if isinstance(v, users.User):
            d[k] = v.email()
    d['_key'] = str(model.key())
    return d


def export_invoices(year, month):
    start_date = datetime.date(year, month, 1)
    end_date = start_date + relativedelta(months=1)

    qry = Invoice.all() \
        .filter('date >=', get_epoch_from_datetime(start_date)) \
        .filter('date <', get_epoch_from_datetime(end_date))

    invoices = list()
    order_keys = set()
    all_products = dict(((p.code, p) for p in Product.all()))
    for invoice_model in qry:
        i = model_to_dict(invoice_model)
        order_key = invoice_model.parent_key().parent()
        i['invoice_number'] = invoice_model.invoice_number
        i['order_items'] = map(model_to_dict, OrderItem.all().ancestor(order_key))
        if invoice_model.charge.is_recurrent:
            # only apply recurrent charges
            for order_item in reversed(i['order_items']):
                order_item['count'] = invoice_model.charge.subscription_extension_length or 1
                product = all_products[order_item['product_code']]
                if not (
                    product.is_subscription_discount or product.is_subscription or product.is_subscription_extension):
                    i['order_items'].remove(order_item)

            # add the subscription extensions like XCTY
            if invoice_model.charge.subscription_extension_order_item_keys:
                known_extension_item_keys = [item['_key'] for item in i['order_items']]

                extension_order_items = db.get(invoice_model.charge.subscription_extension_order_item_keys)
                for item in extension_order_items:
                    item.count = 1
                    if str(item.key()) not in known_extension_item_keys:
                        i['order_items'].append(model_to_dict(item))

        i['order_key'] = order_key
        i['currency'] = invoice_model.currency_code
        order_keys.add(order_key)
        invoices.append(i)

    orders = {o.key(): o for o in db.get(order_keys)}

    contact_keys = set()
    customer_keys = set()
    for i in invoices:
        order_model = orders[i['order_key']]
        del i['order_key']
        i['customer_key'] = order_model.customer_key
        i['contact_key'] = order_model.contact_key
        i['manager'] = None if not order_model.manager else order_model.manager.email()
        customer_keys.add(order_model.customer_key)
        contact_keys.add(order_model.contact_key)

    del orders

    customer_and_contact_models = {m.key(): m for m in db.get(customer_keys.union(contact_keys))}

    # filter invoices for customers of resellers
    reseller_ids = [k.id() for k in LegalEntity.list_non_mobicage(keys_only=True)]
    reseller_team_ids = [t.id for t in RegioManagerTeam.all().filter('legal_entity_id IN', reseller_ids)]

    for i in reversed(invoices):
        customer_model = customer_and_contact_models[i['customer_key']]
        if customer_model.team_id in reseller_team_ids:
            invoices.remove(i)
            continue
        del i['customer_key']
        i['customer'] = model_to_dict(customer_model)
        contact_model = customer_and_contact_models[i['contact_key']]
        del i['contact_key']
        i['contact'] = model_to_dict(contact_model)

    del customer_and_contact_models

    return sorted(invoices,
                  key=lambda i: int(i['invoice_number'].split('.')[-1]))


def export_products():
    products = list()
    for product_model in Product.all():
        p = model_to_dict(product_model)
        p['product_code'] = product_model.code
        p['description'] = product_model.description(u'nl')
        p['default_comment'] = product_model.default_comment(u'nl')
        products.append(p)
    return products


class GenerateQRCodesHandler(webapp2.RequestHandler):

    def get(self):
        current_user = gusers.get_current_user()
        if not is_admin(current_user):
            self.abort(403)
        path = os.path.join(os.path.dirname(__file__), 'html', 'generate_qr_codes.html')
        context = get_shop_context()
        self.response.out.write(template.render(path, context))


class AppBroadcastHandler(webapp2.RequestHandler):

    def get(self):
        current_user = gusers.get_current_user()
        if not is_admin(current_user):
            self.abort(403)
        path = os.path.join(os.path.dirname(__file__), 'html', 'app_broadcast.html')
        context = get_shop_context()
        self.response.out.write(template.render(path, context))


class CustomerMapHandler(webapp2.RequestHandler):

    def get(self, app_id):
        path = os.path.join(os.path.dirname(__file__), 'html', 'customer_map.html')
        settings = get_server_settings()
        lang = get_languages_from_request(self.request)[0]
        translations = {
            'merchants': shop_translate(lang, 'merchants'),
            'merchants_with_terminal': shop_translate(lang, 'merchants_with_terminal'),
            'community_services': shop_translate(lang, 'community_services'),
            'care': shop_translate(lang, 'care'),
            'associations': shop_translate(lang, 'associations'),
        }
        params = {
            'maps_key': settings.googleMapsKey,
            'app_id': app_id,
            'translations': json.dumps(translations)
        }
        self.response.out.write(template.render(path, params))


@cached(2, 21600)
@returns(unicode)
@arguments(app_id=unicode)
def get_customer_locations_for_app(app_id):
    query_string = (u'app_ids:"%s"' % app_id)
    query = search.Query(query_string=query_string,
                         options=search.QueryOptions(returned_fields=['service', 'name', 'location', 'description'],
                                                     limit=1000))
    search_result = search.Index(name=SERVICE_LOCATION_INDEX).search(query)

    customers = {customer.service_email: customer for customer in Customer.list_by_app_id(app_id)}

    def map_result(service_search_result):
        customer_location = CustomerLocationTO()
        for field in service_search_result.fields:
            if field.name == 'service':
                customer = customers.get(field.value.split('/')[0])
                if customer:
                    customer_location.has_terminal = customer.has_loyalty
                    customer_location.address = customer.address1
                    customer_location.type = customer.organization_type
                    if customer.address2:
                        customer_location.address += '\n%s' % customer.address2
                    if customer.zip_code or customer.city:
                        customer_location.address += '\n'
                        if customer.zip_code:
                            customer_location.address += customer.zip_code
                        if customer.zip_code and customer.city:
                            customer_location.address += ' '
                        if customer.city:
                            customer_location.address += customer.city
                else:
                    customer_location.type = ServiceProfile.ORGANIZATION_TYPE_PROFIT
                continue
            if field.name == 'name':
                customer_location.name = field.value
                continue
            if field.name == 'location':
                customer_location.lat = field.value.latitude
                customer_location.lon = field.value.longitude
                continue
            if field.name == 'description':
                customer_location.description = field.value
                continue
        return customer_location

    return json.dumps(serialize_complex_value([map_result(r) for r in search_result.results], CustomerLocationTO, True))


class CustomerMapServicesHandler(webapp2.RequestHandler):

    def get(self, app_id):
        customer_locations = get_customer_locations_for_app(app_id)
        self.response.write(customer_locations)


@rest('/unauthenticated/loyalty/scanned', 'get', read_only_access=True, authenticated=False)
@returns(ReturnStatusTO)
@arguments(user_email_hash=unicode, merchant_email=unicode, app_id=unicode)
def rest_loyalty_scanned(user_email_hash, merchant_email, app_id):
    try:
        bizz_check(user_email_hash is not MISSING, 'user_email_hash is required')
        bizz_check(merchant_email is not MISSING, 'merchant_email is required')
        bizz_check(app_id is not MISSING, 'app_id is required')

        user_code = user_code_by_hash(binascii.unhexlify(user_email_hash))
        profile_pointer = ProfilePointer.get(user_code)
        if not profile_pointer:
            logging.debug('No ProfilePointer found with user_code %s', user_code)
            raise BusinessException('User not found')
        app_user = profile_pointer.user

        bizz_check(get_app_by_id(app_id), 'App not found')
        bizz_check(app_id == get_app_id_from_app_user(profile_pointer.user), 'Invalid user email hash')

        merchant_found = False
        for customer in Customer.list_by_user_email(merchant_email):
            merchant_found = True
            service_user = users.User(customer.service_email)
            logging.info('Received loyalty scan of %s by %s (%s)', app_user, service_user, customer.user_email)
            makeFriends(service_user, app_user, None, None, ORIGIN_USER_INVITE,
                        notify_invitee=False,
                        notify_invitor=False,
                        allow_unsupported_apps=True)

        bizz_check(merchant_found, 'Merchant not found')
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)
    else:
        return RETURNSTATUS_TO_SUCCESS


class PublicPageHandler(webapp2.RequestHandler):

    @property
    def language(self):
        return get_languages_from_request(self.request)[0]

    def translate(self, key, **kwargs):
        return shop_translate(self.language, key, **kwargs)

    def render(self, template_name, **params):
        if not params.get('language'):
            params['language'] = self.language
        app_id = self.request.route_kwargs.get('app_id')
        params['app_id'] = app_id or ''
        routes = ['signin', 'signup', 'reset_password', 'set_password']
        for route_name in routes:
            if app_id:
                url = self.url_for(route_name + '_app', app_id=app_id)
            else:
                url = self.url_for(route_name)
            params[route_name + '_url'] = url
        template_path = 'public/%s.html' % template_name
        return SHOP_JINJA_ENVIRONMENT.get_template(template_path).render(params)

    def return_error(self, message, **kwargs):
        translated_message = self.translate(message, **kwargs)
        self.response.out.write(self.render('error', message=translated_message))

    def dispatch(self):
        if users.get_current_user():
            return self.redirect('/')
        return super(PublicPageHandler, self).dispatch()


class CustomerSigninHandler(PublicPageHandler):

    def get(self, app_id=''):
        self.response.write(self.render('signin'))


class CustomerSignupHandler(PublicPageHandler):

    def get(self, app_id=''):
        language = (self.request.get('language') or self.language).split('_')[0]

        email = self.request.get('email')
        if email.endswith('.'):
            email = email[:-1]
        data = self.request.get('data')
        if email and data:
            # TODO: can be removed after june 2020
            try:
                complete_customer_signup(email, data)
            except ExpiredUrlException:
                return self.return_error("link_expired", action='')
            except AlreadyUsedUrlException:
                return self.return_error("link_is_already_used", action='')
            except InvalidUrlException:
                return self.return_error('invalid_url')

            params = {
                'email_verified': True,
            }
        else:
            apps = []
            # If app id is in the url, only allow choosing that app in the dropdown list.
            if app_id:
                app = get_app_by_id(app_id)
                if app:
                    apps = [app]
            if not apps:
                apps = get_all_signup_enabled_apps()
            solution_server_settings = get_solution_server_settings()
            version = get_current_document_version(DOC_TERMS_SERVICE)
            legal_language = get_legal_language(language)
            params = {
                'apps': sorted(apps, key=lambda x: x.name),
                'recaptcha_site_key': solution_server_settings.recaptcha_site_key,
                'email_verified': False,
                'toc_content': get_version_content(legal_language, DOC_TERMS_SERVICE, version)
            }
        params['language'] = language.lower()
        params['languages'] = [
            (code, name) for code, name in OFFICIALLY_SUPPORTED_LANGUAGES.iteritems() if code in LEGAL_LANGUAGES
        ]
        params['signup_success'] = json.dumps(self.render('signup_success', language=language))
        self.response.write(self.render('signup', **params))


class CustomerSignupPasswordHandler(PublicPageHandler):

    def get(self, app_id=''):
        data = self.request.get('data')
        email = self.request.get('email').rstrip('.')

        params = {
            'email': email,
            'data': data,
            'language': self.language,
            'error': None,
        }
        self.response.write(self.render('signup_setpassword', **params))

    def post(self, app_id=''):
        json_data = json.loads(self.request.body)
        email = json_data.get('email')
        data = json_data.get('data')
        password = json_data.get('password', '')
        password_confirm = json_data.get('password_confirm')
        error = None
        try:
            signup, _ = get_customer_signup(email, data)  # type: CustomerSignup, dict
        except ExpiredUrlException:
            error = self.translate('link_expired', action='')
        except AlreadyUsedUrlException:
            error = self.translate('link_is_already_used', action='')
        except InvalidUrlException:
            error = self.translate('invalid_url')
        if len(password) < 8:
            error = self.translate('password_length_error', length=8)
        elif password != password_confirm:
            error = self.translate('password_match_error')
        if not error:
            tos_version = get_current_document_version(DOC_TERMS_SERVICE)
            result = do_create_service(signup.city_customer, signup.language, True, signup, password, tos_version=tos_version)
            if result.success:
                service_email = result.data['service_email']
                deferred.defer(complete_customer_signup, email, data, service_email)

                try:
                    # Sleep to allow datastore indexes to update
                    time.sleep(2)
                    secret, _ = create_session(users.User(signup.company_email), ignore_expiration=True, cached=False)
                    server_settings = get_server_settings()
                    set_cookie(self.response, server_settings.cookieSessionName, secret)
                except:
                    logging.error("Failed to create session", exc_info=True)
        else:
            result = WarningReturnStatusTO.create(False, error)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(result.to_dict()))


class CustomerResetPasswordHandler(PublicPageHandler):

    def get(self, app_id=''):
        self.response.out.write(self.render('reset_password'))


class CustomerSetPasswordHandler(PublicPageHandler, SetPasswordHandler):
    """Inherit PublicPageHandler first to override SetPasswordHandler return_error()"""

    def get(self, app_id=''):
        email = self.request.get('email')
        data = self.request.get('data')

        try:
            parsed_data = self.parse_and_validate_data(email, data)
        except ExpiredUrlException as e:
            return self.return_error("link_expired", action=e.action)
        except AlreadyUsedUrlException as e:
            return self.return_error("link_is_already_used", action=e.action)
        except InvalidUrlException:
            return self.return_error('invalid_url')

        params = {
            'name': parsed_data['n'],
            'email': email,
            'action': parsed_data['a'],
            'data': data,
        }

        self.response.out.write(self.render('set_password', **params))

    def post(self, app_id=''):
        super(CustomerSetPasswordHandler, self).post()


@rest('/unauthenticated/osa/customer/signup', 'post', read_only_access=True, authenticated=False)
@returns(ReturnStatusTO)
@arguments(city_customer_id=(int, long), company=CompanyTO, customer=CustomerTO, recaptcha_token=unicode,
           email_consents=dict)
def customer_signup(city_customer_id, company, customer, recaptcha_token, email_consents=None):
    try:
        headers = get_headers_for_consent(GenericRESTRequestHandler.getCurrentRequest())
        create_customer_signup(city_customer_id, company, customer, recaptcha_token,
                               domain=get_current_http_host(with_protocol=True), headers=headers, accept_missing=True)
        headers = get_headers_for_consent(GenericRESTRequestHandler.getCurrentRequest())
        consents = email_consents or {}
        context = u'User signup'
        try_or_defer(update_customer_consents, customer.user_email, consents, headers, context)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


def parse_euvat_address_eu(address):
    address = address.strip().splitlines()
    zc_ci = address.pop()
    zip_code, city = zc_ci.split(' ', 1)
    address1 = address.pop(0) if len(address) > 0 else ''
    address2 = address.pop(0) if len(address) > 0 else ''
    return address1, address2, zip_code, city


@rest('/unauthenticated/osa/signup/app-info/<app_id:[^/]+>', 'get', read_only_access=True, authenticated=False)
@returns(dict)
@arguments(app_id=unicode, language=unicode)
def get_customer_info(app_id, language=None):
    app = get_app_by_id(app_id)
    if not app:
        raise HttpNotFoundException('app_not_found', {'app_id': app_id})
    if not language:
        request = GenericRESTRequestHandler.getCurrentRequest()
        language = get_languages_from_request(request)[0]
    customer = Customer.get_by_service_email(app.main_service)  # type: Customer
    organization_types = dict(get_organization_types(customer, language))
    return {
        'customer': {
            'id': customer.id,
            'country': customer.country,
        },
        'organization_types': organization_types
    }


@rest('/unauthenticated/osa/signup/privacy-settings/<app_id:[^/]+>', 'get', read_only_access=True, authenticated=False)
@returns([PrivacySettingsGroupTO])
@arguments(app_id=unicode, language=unicode)
def get_privacy_settings(app_id, language=None):
    if not language:
        request = GenericRESTRequestHandler.getCurrentRequest()
        language = get_languages_from_request(request)[0]
    return get_consents_for_app(app_id, language, [])


class QuotationHandler(webapp2.RequestHandler):

    def get(self, customer_id, quotation_id):
        customer_id = long(customer_id)
        quotation_id = long(quotation_id)
        quotation = db.get(Quotation.create_key(quotation_id, customer_id))
        if not quotation:
            self.abort(404)
        bucket = get_solution_server_settings().shop_gcs_bucket
        url = Quotation.download_url(Quotation.filename(bucket, customer_id, quotation_id)).encode('ascii')
        logging.info('Redirection to %s', url)
        self.redirect(url)


class CustomerCirkloAcceptHandler(PublicPageHandler):

    def get_url(self, customer):
        url_params = urllib.urlencode({'cid': customer.id})
        return '/customers/consent/cirklo?{}'.format(url_params)

    def dispatch(self):
        # Don't redirect to dashboard when logged in
        return super(PublicPageHandler, self).dispatch()

    def get(self):
        customer_id = self.request.get('cid')
        if customer_id:
            try:
                customer = Customer.get_by_id(long(customer_id))
            except:
                return self.return_error('invalid_url')
        else:
            email = self.request.get('email')
            data = self.request.get('data')

            try:
                data = validate_customer_url_data(email, data)
            except InvalidUrlException:
                return self.return_error('invalid_url')

            customer = db.get(data['s']) # Customer
        if not customer:
            return self.abort(404)

        consents = get_customer_consents(customer.user_email)
        should_accept = False
        if SolutionServiceConsent.TYPE_CITY_CONTACT not in consents.types:
            consents.types.append(SolutionServiceConsent.TYPE_CITY_CONTACT)
            should_accept = True
        if SolutionServiceConsent.TYPE_CIRKLO_SHARE not in consents.types:
            consents.types.append(SolutionServiceConsent.TYPE_CIRKLO_SHARE)
            should_accept = True
        params = {
            'cirklo_accept_url': self.get_url(customer),
            'should_accept': should_accept
        }

        self.response.out.write(self.render('cirklo_accept', **params))

    def post(self):
        from solutions.common.dal.cityapp import get_service_user_for_city
        try:
            customer_id = self.request.get('cid')
            customer = Customer.get_by_id(long(customer_id))
            if not customer:
                raise Exception('Customer not found')
        except:
            self.redirect('/')
            return

        consents = get_customer_consents(customer.user_email)
        should_put_consents = False
        if SolutionServiceConsent.TYPE_CITY_CONTACT not in consents.types:
            consents.types.append(SolutionServiceConsent.TYPE_CITY_CONTACT)
            should_put_consents = True
        if SolutionServiceConsent.TYPE_CIRKLO_SHARE not in consents.types:
            consents.types.append(SolutionServiceConsent.TYPE_CIRKLO_SHARE)
            should_put_consents = True

        if should_put_consents:
            consents.put()

            service_user = get_service_user_for_city(customer.default_app_id)
            city_id = CirkloCity.get_by_service_email(service_user.email()).city_id

            service_user_email = customer.service_user.email()
            cirklo_merchant_key = CirkloMerchant.create_key(service_user_email)
            cirklo_merchant = cirklo_merchant_key.get()  # type: CirkloMerchant
            if not cirklo_merchant:
                cirklo_merchant = CirkloMerchant(key=cirklo_merchant_key)  # type: CirkloMerchant
                cirklo_merchant.denied = False
            cirklo_merchant.creation_date = datetime.datetime.utcfromtimestamp(customer.creation_time)
            cirklo_merchant.service_user_email = service_user_email
            cirklo_merchant.customer_id = customer.id
            cirklo_merchant.city_id = city_id
            cirklo_merchant.data = None
            cirklo_merchant.whitelisted = check_merchant_whitelisted(city_id, customer.user_email)
            cirklo_merchant.put()

            service_identity_user = create_service_identity_user(customer.service_user)
            try_or_defer(re_index_map_only, service_identity_user)

        self.redirect(self.get_url(customer))


class VouchersCirkloSignupHandler(PublicPageHandler):

    def get(self, city_id=''):
        supported_languages = ["nl", "fr"]
        language = (self.request.get('language') or self.language).split('_')[0].lower()

        cities = []
        if city_id and city_id != 'staging':
            city = CirkloCity.create_key(city_id).get()
            if city:
                cities = [city]
        if not cities:
            if city_id and city_id == 'staging':
                cities = [city for city in CirkloCity.list_signup_enabled() if city.city_id.startswith('staging-')]
            else:
                cities = [city for city in CirkloCity.list_signup_enabled() if not city.city_id.startswith('staging-')]
        solution_server_settings = get_solution_server_settings()
        if language not in supported_languages:
            language = supported_languages[0]
        if language == 'fr':
            sorted_cities = sorted(cities, key=lambda x: x.signup_names.fr)
        else:
            sorted_cities = sorted(cities, key=lambda x: x.signup_names.nl)
        params = {
            'city_id': city_id or None,
            'cities': sorted_cities,
            'recaptcha_site_key': solution_server_settings.recaptcha_site_key,
            'language': language,
            'languages': [(code, name) for code, name in OFFICIALLY_SUPPORTED_LANGUAGES.iteritems()
                          if code in supported_languages]
        }

        md = Markdown(output='html', extensions=['nl2br', NewTabExtension()])
        lines = [
            '#### %s' % translate(language, 'cirklo_info_title'),
            '<br />',
            translate(language, 'cirklo_info_text_signup'),
            '',
            translate(language, 'cirklo_participation_text_signup'),
        ]

        params['privacy_settings'] = {
            'cirklo': {
                'label': translate(language, 'consent_cirklo_share'),
                'description': md.convert('\n\n'.join(lines))
            },
            'city': {
                'label': translate(language, 'consent_city_contact'),
                'description': '<h4>%s</h4>' % translate(language, 'consent_share_with_city')
            }
        }

        params['signup_success'] = md.convert('\n\n'.join([translate(language, 'cirklo.signup.success')]))

        self.response.write(self.render('cirklo_signup', **params))

    def post(self):
        json_data = json.loads(self.request.body)
        logging.debug(json_data)

        if not recaptcha_verify(json_data['recaptcha_token']):
            logging.debug('Cannot verify recaptcha response')
            self.abort(400)

        if not CirkloCity.create_key(json_data['city_id']).get():
            logging.debug('CirkloCity was invalid')
            self.abort(400)

        merchant = CirkloMerchant()
        merchant.service_user_email = None
        merchant.customer_id = -1
        merchant.city_id = json_data['city_id']
        merchant.data = {
            u'company': json_data['company'],
            u'language': json_data['language']
        }
        merchant.whitelisted = check_merchant_whitelisted(json_data['city_id'], json_data['company']['email'])
        merchant.denied = False
        merchant.put()

        self.response.headers['Content-Type'] = 'text/json'
        return self.response.out.write(json.dumps({'success': True, 'errormsg': None}))
