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

import webapp2
from babel import Locale
from google.appengine.api import search, users as gusers
from google.appengine.ext import db
from google.appengine.ext.deferred import deferred
from google.appengine.ext.webapp import template
from markdown import Markdown

from mcfw.cache import cached
from mcfw.consts import MISSING
from mcfw.exceptions import HttpNotFoundException
from mcfw.restapi import rest, GenericRESTRequestHandler
from mcfw.rpc import serialize_complex_value, arguments, returns
from rogerthat.bizz.communities.communities import get_communities_by_country, get_community, get_community_countries
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
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import bizz_check, try_or_defer, get_country_code_by_ipaddress
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.cookie import set_cookie
from rogerthat.utils.service import create_service_identity_user
from shop import SHOP_JINJA_ENVIRONMENT
from shop.bizz import create_customer_signup, complete_customer_signup, get_organization_types, \
    update_customer_consents, get_customer_signup, validate_customer_url_data, \
    get_customer_consents
from shop.business.permissions import is_admin
from shop.constants import OFFICIALLY_SUPPORTED_LANGUAGES
from shop.models import Customer
from shop.to import CompanyTO, CustomerTO, CustomerLocationTO
from shop.view import get_shop_context, get_current_http_host
from solution_server_settings import get_solution_server_settings
from solutions import translate
from solutions.common.bizz.grecaptcha import recaptcha_verify
from solutions.common.bizz.settings import get_consents_for_community
from solutions.common.integrations.cirklo.cirklo import check_merchant_whitelisted
from solutions.common.integrations.cirklo.models import CirkloMerchant, CirkloCity
from solutions.common.markdown_newtab import NewTabExtension
from solutions.common.models import SolutionServiceConsent
from solutions.common.restapi.services import do_create_service
from solutions.common.to.settings import PrivacySettingsGroupTO


class StaticFileHandler(webapp2.RequestHandler):

    def get(self, filename):
        cur_path = os.path.dirname(__file__)
        path = os.path.join(cur_path, u'html', filename)
        with open(path, 'r') as f:
            self.response.write(f.read())


class GenerateQRCodesHandler(webapp2.RequestHandler):

    def get(self):
        current_user = gusers.get_current_user()
        if not is_admin(current_user):
            self.abort(403)
        path = os.path.join(os.path.dirname(__file__), 'html', 'generate_qr_codes.html')
        context = get_shop_context()
        self.response.out.write(template.render(path, context))


class CustomerMapHandler(webapp2.RequestHandler):

    def get(self, app_id):
        path = os.path.join(os.path.dirname(__file__), 'html', 'customer_map.html')
        settings = get_server_settings()
        lang = get_languages_from_request(self.request)[0]
        translations = {
            'merchants': translate(lang, 'merchants'),
            'merchants_with_terminal': translate(lang, 'merchants_with_terminal'),
            'community_services': translate(lang, 'community_services'),
            'care': translate(lang, 'care'),
            'associations': translate(lang, 'associations'),
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
        return translate(self.language, key, **kwargs)

    def render(self, template_name, **params):
        if not params.get('language'):
            params['language'] = self.language
        routes = ['signin', 'signup', 'reset_password', 'set_password']
        for route_name in routes:
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

    def get(self, app_id=None):
        self.response.write(self.render('signin'))


class CustomerSignupHandler(PublicPageHandler):

    def get(self):
        language = (self.request.get('language') or self.language).split('_')[0]
        if language not in LEGAL_LANGUAGES:
            language = DEFAULT_LANGUAGE
        solution_server_settings = get_solution_server_settings()
        version = get_current_document_version(DOC_TERMS_SERVICE)
        legal_language = get_legal_language(language)
        countries = get_community_countries()
        selected_country = get_country_code_by_ipaddress(os.environ.get('HTTP_X_FORWARDED_FOR', None))
        if selected_country:
            communities = get_communities_by_country(selected_country)
        else:
            communities = []
        params = {
            'recaptcha_site_key': solution_server_settings.recaptcha_site_key,
            'email_verified': False,
            'toc_content': get_version_content(legal_language, DOC_TERMS_SERVICE, version),
            'language': language.lower(),
            'languages': [(code, name) for code, name in OFFICIALLY_SUPPORTED_LANGUAGES.iteritems()
                          if code in LEGAL_LANGUAGES],
            'countries': [(country, Locale(language, country).get_territory_name()) for country in countries],
            'communities': communities,
            'selected_country': selected_country,
            'signup_success': json.dumps(self.render('signup_success', language=language))
        }
        self.response.write(self.render('signup', **params))


class CustomerSignupPasswordHandler(PublicPageHandler):

    def get(self):
        data = self.request.get('data')
        email = self.request.get('email').rstrip('.')

        params = {
            'email': email,
            'data': data,
            'language': self.language,
            'error': None,
        }
        self.response.write(self.render('signup_setpassword', **params))

    def post(self):
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

    def get(self):
        self.response.out.write(self.render('reset_password'))


class CustomerSetPasswordHandler(PublicPageHandler, SetPasswordHandler):
    """Inherit PublicPageHandler first to override SetPasswordHandler return_error()"""

    def get(self):
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

    def post(self):
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


@rest('/unauthenticated/osa/signup/community-info/<community_id:[^/]+>', 'get', read_only_access=True,
      authenticated=False)
@returns(dict)
@arguments(community_id=(int, long), language=unicode)
def get_customer_info(community_id, language=None):
    community = get_community(community_id)
    if not community:
        raise HttpNotFoundException('Community not found')
    if not language:
        request = GenericRESTRequestHandler.getCurrentRequest()
        language = get_languages_from_request(request)[0]
    customer = Customer.get_by_service_email(community.main_service)  # type: Customer
    organization_types = dict(get_organization_types(customer, community.default_app, language))
    return {
        'customer': {
            'id': customer.id,
        },
        'organization_types': organization_types
    }


@rest('/unauthenticated/osa/signup/communities/<country_code:[^/]+>', 'get', read_only_access=True, authenticated=False)
@returns([dict])
@arguments(country_code=unicode)
def api_get_communities(country_code):
    return [{'name': community.name, 'id': community.id} for community in get_communities_by_country(country_code)]


@rest('/unauthenticated/osa/signup/privacy-settings/<community_id:[^/]+>', 'get', read_only_access=True,
      authenticated=False)
@returns([PrivacySettingsGroupTO])
@arguments(community_id=(int, long), language=unicode)
def get_privacy_settings(community_id, language=None):
    if not language:
        request = GenericRESTRequestHandler.getCurrentRequest()
        language = get_languages_from_request(request)[0]
    return get_consents_for_community(community_id, language, [])


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
        try:
            customer_id = self.request.get('cid')
            customer = Customer.get_by_id(long(customer_id))  # type: Customer
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

            community = get_community(customer.community_id)
            city_id = CirkloCity.get_by_service_email(community.main_service).city_id

            service_user_email = customer.service_user.email()
            cirklo_merchant_key = CirkloMerchant.create_key(service_user_email)
            cirklo_merchant = cirklo_merchant_key.get()  # type: CirkloMerchant
            if not cirklo_merchant:
                cirklo_merchant = CirkloMerchant(key=cirklo_merchant_key)  # type: CirkloMerchant
                cirklo_merchant.denied = False
                logging.debug('Creating new cirklo merchant')
            cirklo_merchant.creation_date = datetime.datetime.utcfromtimestamp(customer.creation_time)
            cirklo_merchant.service_user_email = service_user_email
            cirklo_merchant.customer_id = customer.id
            cirklo_merchant.city_id = city_id
            cirklo_merchant.data = None
            cirklo_merchant.whitelisted = check_merchant_whitelisted(city_id, customer.user_email)
            cirklo_merchant.put()
            logging.debug('Saving cirklo merchant: %s', cirklo_merchant)

            service_identity_user = create_service_identity_user(customer.service_user)
            try_or_defer(re_index_map_only, service_identity_user)
        else:
            logging.debug('Not saving cirklo merchant, consents:', consents)

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

        self.response.headers['Content-Type'] = 'text/json'
        found_in_db = check_merchant_whitelisted(json_data['city_id'], json_data['company']['email'])
        if found_in_db:
            logging.debug('email found in cirklo db')
        else:
            cirklo_merchant = CirkloMerchant.get_by_city_id_and_email(json_data['city_id'], json_data['company']['email'])
            if cirklo_merchant:
                logging.debug('email found in osa db')
                found_in_db = True

        if found_in_db:
            return self.response.out.write(json.dumps({'success': False, 'errormsg': translate(json_data['language'], 'cirklo.email_already_used')}))

        merchant = CirkloMerchant()
        merchant.service_user_email = None
        merchant.customer_id = -1
        merchant.city_id = json_data['city_id']
        merchant.data = {
            u'company': json_data['company'],
            u'language': json_data['language']
        }
        merchant.emails = [json_data['company']['email']]
        merchant.whitelisted = check_merchant_whitelisted(json_data['city_id'], json_data['company']['email'])
        merchant.denied = False
        merchant.put()

        self.response.headers['Content-Type'] = 'text/json'
        return self.response.out.write(json.dumps({'success': True, 'errormsg': None}))
