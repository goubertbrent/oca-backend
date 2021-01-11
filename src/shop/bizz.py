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

import hashlib
import json
import urllib
import urlparse
from collections import OrderedDict
from functools import partial
from types import NoneType

import base64
import cloudstorage
import csv
import datetime
import logging
from babel.dates import format_datetime, get_timezone, format_date
from google.appengine.api import urlfetch
from google.appengine.ext import deferred, db, ndb

from mcfw.exceptions import HttpBadRequestException
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.communities.models import Community
from rogerthat.bizz.elasticsearch import get_elasticsearch_config, create_index, \
    delete_index, es_request, index_doc
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.bizz.maps.services import SearchTag
from rogerthat.bizz.profile import update_password_hash, create_user_profile, get_service_profile
from rogerthat.bizz.rtemail import EMAIL_REGEX
from rogerthat.consts import FAST_QUEUE, OFFICIALLY_SUPPORTED_COUNTRIES, DEBUG, EXPORTS_BUCKET
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.app import get_app_settings, get_app_by_id, get_app_name_by_id
from rogerthat.dal.profile import get_service_or_user_profile, get_user_profile
from rogerthat.dal.service import get_default_service_identity
from rogerthat.exceptions.login import AlreadyUsedUrlException, InvalidUrlException, ExpiredUrlException
from rogerthat.models import App, ServiceIdentity, ServiceProfile, UserProfile, Message
from rogerthat.models.settings import SyncedNameValue
from rogerthat.pages.legal import get_current_document_version, DOC_TERMS_SERVICE
from rogerthat.restapi.user import get_reset_password_url_params
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.to.messaging import AnswerTO
from rogerthat.translations import DEFAULT_LANGUAGE, localize
from rogerthat.utils import bizz_check, now, channel, generate_random_key, send_mail, \
    get_server_url
from rogerthat.utils.crypto import encrypt, decrypt, sha256_hex
from rogerthat.utils.transactions import run_in_transaction, run_in_xg_transaction, run_after_transaction
from shop import SHOP_JINJA_ENVIRONMENT
from shop.business.i18n import shop_translate
from shop.constants import OFFICIALLY_SUPPORTED_LANGUAGES
from shop.exceptions import BusinessException, CustomerNotFoundException, ContactNotFoundException, \
    InvalidEmailFormatException, EmptyValueException, \
    InvalidServiceEmailException, InvalidLanguageException, DuplicateCustomerNameException, \
    NotOperatingInCountryException, NoPermissionException
from shop.models import Customer, Contact, normalize_vat, CustomerSignup, LegalDocumentAcceptance, LegalDocumentType
from shop.to import CustomerServiceTO, CompanyTO, CustomerTO
from solution_server_settings import get_solution_server_settings, CampaignMonitorWebhook
from solutions import translate as common_translate, translate
from solutions.common.bizz import SolutionModule, campaignmonitor
from solutions.common.bizz.grecaptcha import recaptcha_verify
from solutions.common.bizz.messaging import send_inbox_forwarders_message
from solutions.common.bizz.service import new_inbox_message, send_signup_update_messages, \
    add_service_consent, remove_service_consent, create_customer_with_service, put_customer_service, \
    get_default_modules, _schedule_signup_smart_emails
from solutions.common.bizz.settings import parse_facebook_url, validate_url
from solutions.common.dal import get_solution_settings
from solutions.common.handlers import JINJA_ENVIRONMENT
from solutions.common.models import SolutionInboxMessage, SolutionServiceConsent
from solutions.common.to import ProvisionResponseTO
from solutions.flex.bizz import create_flex_service

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def create_customer_index():
    index = {
        'mappings': {
            'properties': {
                'customer': {
                    'type': 'keyword'
                },
                'service': {
                    'type': 'keyword'
                },
                'contact': {
                    'type': 'keyword'
                },
                'address': {
                    'type': 'keyword'
                },
                'full_matches': {
                    'type': 'keyword',
                },
                'tags': {
                    'type': 'keyword'
                },
                'txt': {
                    'type': 'text'
                },
                'organization_type': {
                    'type': 'keyword'
                },
            }
        }
    }
    config = get_elasticsearch_config()
    return create_index(config.shop_customers_index, index)


def delete_customer_index():
    config = get_elasticsearch_config()
    return delete_index(config.shop_customers_index)


@returns([Customer])
@arguments(search_string=unicode, community_ids=[(int, long)], limit=(int, long), organization_type=(int, long))
def search_customer(search_string, community_ids, limit=20, organization_type=None):
    qry = {
        'size': limit,
        'from': 0,
        '_source': {
            'includes': ['tags'],
        },
        'query': {
            'bool': {
                'must': [],
                'filter': [],
                'should': []
            }
        },
        'sort': [
            '_score',
        ]
    }
    if search_string.strip():
        qry['query']['bool']['must'].append({
            'multi_match': {
                'query': search_string,
                'fields': ['full_matches^600', 'customer^400', 'service^200', 'contact^100', 'address^50', 'txt'],
                'fuzziness': '1'
            }
        })

    if organization_type is not None:
        qry['query']['bool']['filter'].append({
            'term': {
                'organization_type': organization_type
            }
        })

    if community_ids:
        community_tags_filter = {
            'bool': {
                'should': [],
                'minimum_should_match': 1
            }
        }
        for community_id in community_ids:
            community_tags_filter['bool']['should'].append({
                'term': {
                    'tags': SearchTag.community(community_id)
                }
            })

        qry['query']['bool']['must'].append(community_tags_filter)

    config = get_elasticsearch_config()
    path = '/%s/_search' % config.shop_customers_index
    result_data = es_request(path, urlfetch.POST, qry)
    customer_keys = list()
    for hit in result_data['hits']['hits']:
        if hit['_score'] < 1.0:
            continue
        customer_id = long(hit['_id'])
        customer_keys.append(Customer.create_key(customer_id))

    tmp_customers = Customer.get(customer_keys)
    customers = []
    missing_customer_keys = set()
    for i, c in enumerate(tmp_customers):
        if not c:
            try:
                missing_customer_keys.add(customer_keys[i].id())
            except:
                missing_customer_keys.add('unknown')
            continue
        customers.append(c)
    if missing_customer_keys:
        logging.error('Found customer(s) in search index that cannot be found in database: %s', missing_customer_keys)
    return customers


@arguments(customer_key=db.Key)
def re_index_customer(customer_key):
    customer = Customer.get(customer_key)
    bizz_check(customer)

    uid = unicode(customer.id)
    doc = {
        'full_matches': [],
        'customer': [],
        'service': [],
        'contact': [],
        'address': [],
        'tags': [],
        'organization_type': customer.organization_type,
    }

    doc['full_matches'].append(str(customer_key.id()))
    doc['customer'].append(customer.name)
    doc['address'].append(' '.join([customer.address1 or '', customer.address2 or '']))
    doc['address'].append(customer.zip_code)
    doc['address'].append(customer.city)

    for contact in Contact.list(customer):
        doc['full_matches'].append(contact.phone_number)
        doc['full_matches'].append(contact.email)
        doc['contact'].append('%s %s' % (contact.first_name, contact.last_name))

    if customer.service_email:
        si = get_default_service_identity(users.User(customer.service_email))
        doc['service'].append(si.name)
        doc['full_matches'].append(customer.user_email)
        doc['full_matches'].append(customer.service_email)
        doc['tags'].append(SearchTag.community(customer.community_id))

    txt = set()
    for k, v in doc.iteritems():
        if k in ('full_matches', 'tags', 'organization_type'):
            continue
        for text in v:
            txt.add(text)

    doc['txt'] = list(txt)

    config = get_elasticsearch_config()
    return index_doc(config.shop_customers_index, uid, doc)


@returns(Customer)
@arguments(customer_id=(int, long, NoneType), vat=unicode, name=unicode, address1=unicode,
           address2=unicode, zip_code=unicode, city=unicode, country=unicode, language=unicode,
           organization_type=(int, long), force=bool, website=unicode, facebook_page=unicode,
           community_id=(int, long, NoneType))
def create_or_update_customer(customer_id, vat, name, address1, address2, zip_code, city, country,
                              language, organization_type, force=False, website=None, facebook_page=None,
                              community_id=0):
    is_in_transaction = db.is_in_transaction()
    name = name.strip()
    if not name:
        raise EmptyValueException('first_name')
    if not country:
        raise EmptyValueException('country')
    if not language:
        raise EmptyValueException('Language')
    if not organization_type:
        raise EmptyValueException('organization_type')
    if country not in OFFICIALLY_SUPPORTED_COUNTRIES:
        raise NotOperatingInCountryException(country)
    if language not in OFFICIALLY_SUPPORTED_LANGUAGES:
        raise InvalidLanguageException(language)
    if not customer_id and not community_id:
        raise EmptyValueException('community_id')

    if customer_id:
        customer = Customer.get_by_id(customer_id)
    else:
        customer = Customer(creation_time=now())

    if community_id:
        customer.community_id = community_id

    if not force:
        @db.non_transactional
        def list_customers_by_name(name):
            # type: (str) -> Iterable[Customer]
            return Customer.list_by_name(name, 20)

        try:
            customer_key = customer.key()
        except db.NotSavedError:
            customer_key = None

        for other_customer in list_customers_by_name(name):
            same_community = other_customer.community_id and other_customer.community_id == community_id
            if customer_key != other_customer.key() and same_community:
                raise DuplicateCustomerNameException(name)

    if vat:
        vat = normalize_vat(country, vat)
    customer.vat = vat
    customer.name = name
    customer.normalized_name = Customer.normalize_name(name)
    customer.address1 = address1
    customer.address2 = address2
    customer.zip_code = zip_code
    customer.city = city
    customer.country = country
    customer.language = language
    customer.organization_type = organization_type
    if website is not None:
        customer.website = website
    if facebook_page is not None:
        customer.facebook_page = facebook_page
    customer.put()

    deferred.defer(re_index_customer, customer.key(), _transactional=is_in_transaction, _queue=FAST_QUEUE)

    return customer


@arguments(service=CustomerServiceTO)
def validate_service(service):
    # type: (CustomerServiceTO) -> None
    if not EMAIL_REGEX.match(service.email):
        raise InvalidEmailFormatException(service.email)
    if not service.language:
        raise EmptyValueException('language')
    if not service.organization_type:
        raise EmptyValueException('organization_type')
    service.email = users.User(service.email).email()


@returns(ProvisionResponseTO)
@arguments(customer_or_id=(int, long, Customer), service=CustomerServiceTO, skip_module_check=bool,
           search_enabled=bool, skip_email_check=bool, broadcast_to_users=[users.User], password=unicode,
           tos_version=(int, long, NoneType))
def put_service(customer_or_id, service, skip_module_check=False, search_enabled=False, skip_email_check=False,
                broadcast_to_users=None, password=None, tos_version=None):
    # type: (Union[int, long, Customer], CustomerServiceTO, bool, bool, bool, List[users.User], unicode, Optional[Union[int, long]]) -> ProvisionResponseTO
    validate_service(service)

    if isinstance(customer_or_id, Customer):
        customer = customer_or_id
    else:
        customer = Customer.get_by_id(customer_or_id)

    customer.managed_organization_types = service.managed_organization_types
    customer.put()
    redeploy = bool(customer.service_email)
    user_existed = False

    if redeploy:
        if customer.user_email != service.email and not skip_email_check:
            raise InvalidServiceEmailException(customer.user_email)
    else:
        p = get_service_or_user_profile(users.User(service.email))
        user_existed = p and isinstance(p, UserProfile)

    modules = service.modules
    if redeploy:
        sln_settings = get_solution_settings(users.User(customer.service_email))
        hidden_modules = SolutionModule.hidden_modules()
        for m in sln_settings.modules:
            if m in hidden_modules and m not in modules:
                modules.append(m)
    if not redeploy:
        # Set the websites only when first creating the service
        websites = []
        if customer.facebook_page:
            fb_url = parse_facebook_url(customer.facebook_page)
            if fb_url:
                page = SyncedNameValue()
                page.value = fb_url
                page.name = common_translate(customer.language, 'Facebook page')
                websites.append(page)
        if customer.website:
            url = validate_url(customer.website)
            if url:
                site = SyncedNameValue()
                site.value = url
                websites.append(site)
    else:
        websites = None

    r = create_flex_service(customer.service_email if redeploy else service.email, customer.name,
                            service.phone_number, [service.language], u'EUR', modules,
                            redeploy, service.organization_type,
                            search_enabled, broadcast_to_users=broadcast_to_users, websites=websites, password=password,
                            tos_version=tos_version, community_id=service.community_id)

    r.auto_login_url = customer.auto_login_url
    send_login_information = False if tos_version else True
    deferred.defer(_after_service_saved, customer.key(), service.email, r, redeploy, service.community_id,
                   broadcast_to_users, bool(user_existed), send_login_information=send_login_information,
                   _transactional=db.is_in_transaction(), _queue=FAST_QUEUE)
    return r


@arguments(customer_key=db.Key, user_email=unicode, r=ProvisionResponseTO, is_redeploy=bool, community_id=(int, long),
           broadcast_to_users=[users.User], user_exists=bool, send_login_information=bool)
def _after_service_saved(customer_key, user_email, r, is_redeploy, community_id, broadcast_to_users, user_exists=False,
                         send_login_information=True):
    # type: (db.Key, unicode, ProvisionResponseTO, bool, int, List[users.User], bool, bool) -> None
    from rogerthat.bizz.news import create_default_news_settings
    sln_settings = get_solution_settings(users.User(r.login))
    community = get_community(community_id)
    customer = Customer.get(customer_key)
    # Remove this service from the admin services when the community id has been updated (only for city services)
    if customer.community_id != community_id and SolutionModule.CITY_APP in sln_settings.modules:
        to_update = App.list_by_admin_service(r.login).fetch(None)  # type: List[App]
        for app in to_update:
            if community.default_app != app.app_id:
                app.admin_services.remove(r.login)
        put_and_invalidate_cache(*to_update)
        deferred.defer(create_default_news_settings, customer.service_user, customer.organization_type, community_id)

    def trans():
        customer = Customer.get(customer_key)
        updated = False
        to_put = []
        if customer.community_id != community_id:
            app = db.get(App.create_key(community.default_app))
            if r.login not in app.admin_services:
                app.admin_services.append(r.login)
                to_put.append(app)
            if SolutionModule.CITY_APP in sln_settings.modules:
                if not is_redeploy:
                    app_settings = get_app_settings(community.default_app)
                    app_settings.birthday_message = common_translate(sln_settings.main_language,
                                                                     u'birthday_message_default_text')
                    to_put.append(app_settings)
            customer.community_id = community_id
            updated = True

        if not customer.community_id or customer.community_id != community_id:
            customer.community_id = community_id
            updated = True

        if not customer.service_email:
            customer.user_email = user_email
            customer.service_email = r.login
            updated = True

        if updated:
            to_put.append(customer)

        deferred.defer(re_index_customer, customer_key, _transactional=True, _queue=FAST_QUEUE)

        if broadcast_to_users:
            channel.send_message(broadcast_to_users, 'shop.provision.success', customer_id=customer.id)

        if send_login_information and not is_redeploy:
            settings = get_server_settings()
            contact = Contact.get_one(customer_key)

            # get the login url that matches the /customers/signin path
            # from settings customSigninPaths for now
            login_url = settings.get_signin_url()
            parsed_login_url = urlparse.urlparse(login_url)
            action = shop_translate(customer.language, 'password_reset')
            reset_password_link = password = None
            if not user_exists:
                reset_password_route = '/customers/setpassword'
                url_params = get_reset_password_url_params(customer.name, users.User(user_email), action=action)
                reset_password_link = '%s://%s%s?%s' % (parsed_login_url.scheme, parsed_login_url.netloc,
                                                        reset_password_route, url_params)
                password = r.password

            # TODO: email with OSA style in header, footer
            params = {
                'language': customer.language,
                'name': contact.first_name + ' ' + contact.last_name,
                'login_url': login_url,
                'user_email': user_email,
                'password': password,
                'reset_password_link': reset_password_link
            }

            text_body = SHOP_JINJA_ENVIRONMENT.get_template('emails/login_information_email.tmpl').render(params)
            html_body = SHOP_JINJA_ENVIRONMENT.get_template('emails/login_information_email_html.tmpl').render(params)

            subject = '%s - %s' % (common_translate(customer.language, 'our-city-app'),
                                   common_translate(customer.language, 'login_information'))
            from_email = '%s <%s>' % (community.name, shop_translate(customer.language, 'oca_info_email_address'))

            send_mail(from_email, user_email, subject, text_body, html=html_body)

        if to_put:
            put_and_invalidate_cache(*to_put)

    run_in_xg_transaction(trans)


@returns(Contact)
@arguments(customer_or_id=(int, long, Customer), first_name=unicode, last_name=unicode, email_address=unicode,
           phone_number=unicode)
def create_contact(customer_or_id, first_name, last_name, email_address, phone_number):
    first_name = first_name.strip()
    last_name = last_name.strip()
    phone_number = phone_number.strip()
    if not first_name:
        raise EmptyValueException('first_name')
    if not email_address:
        raise EmptyValueException('email_address')
    if not phone_number:
        raise EmptyValueException('Phone number')
    if not EMAIL_REGEX.match(email_address):
        raise InvalidEmailFormatException(email_address)

    if isinstance(customer_or_id, Customer):
        customer = customer_or_id
    else:
        customer = Customer.get_by_id(customer_or_id)

    contact = Contact(parent=customer)
    contact.first_name = first_name
    contact.last_name = last_name
    contact.email = email_address
    contact.phone_number = phone_number
    contact.put()

    deferred.defer(re_index_customer, customer.key(), _transactional=db.is_in_transaction(), _queue=FAST_QUEUE)
    return contact


@returns(Contact)
@arguments(customer_id=(int, long), contact_id=(int, long), first_name=unicode, last_name=unicode,
           email_address=unicode, phone_number=unicode)
def update_contact(customer_id, contact_id, first_name, last_name, email_address, phone_number):
    first_name = first_name.strip()
    last_name = last_name.strip()
    phone_number = phone_number.strip()
    if not first_name:
        raise EmptyValueException('first_name')
    if not email_address:
        raise EmptyValueException('email_address')
    if not phone_number:
        raise EmptyValueException('Phone number')

    def trans():
        customer, contact = db.get([Customer.create_key(customer_id), Contact.create_key(contact_id, customer_id)])
        if not customer:
            raise CustomerNotFoundException(customer_id)
        if not contact:
            raise ContactNotFoundException(contact_id)
        contact.first_name = first_name
        contact.last_name = last_name
        contact.email = email_address
        contact.phone_number = phone_number
        contact.put()
        deferred.defer(re_index_customer, customer.key(), _transactional=True, _queue=FAST_QUEUE)
        return contact

    return run_in_transaction(trans)


@returns()
@arguments(customer_id=(int, long), contact_id=(int, long))
def delete_contact(customer_id, contact_id):
    customer, contact = db.get([Customer.create_key(customer_id), Contact.create_key(contact_id, customer_id)])
    if not customer:
        raise CustomerNotFoundException(customer_id)
    if contact:
        contact.delete()


@returns(db.Query)
@arguments()
def get_all_customers():
    return Customer.all().order('-creation_time')


def export_customers_csv(google_user):
    result = list()
    properties = ['name', 'address1', 'address2', 'zip_code', 'country']

    phone_numbers = {}
    qry = Contact.all()
    while True:
        contacts = qry.fetch(300)
        if not contacts:
            break
        for contact in contacts:
            phone_numbers[contact.customer_key.id()] = contact.phone_number
        qry.with_cursor(qry.cursor())

    qry = get_all_customers()
    communities = {community.id: community for community in Community.query()}
    while True:
        customers = qry.fetch(300)
        if not customers:
            break
        logging.debug('Fetched %s customers', len(customers))
        qry.with_cursor(qry.cursor())
        for customer in customers:
            d = OrderedDict()
            d['Email'] = customer.user_email
            d['Customer since'] = format_datetime(customer.creation_time, 'yyyy-MM-dd HH:mm:ss',
                                                  tzinfo=get_timezone('Europe/Brussels'))
            for p in properties:
                d[p] = getattr(customer, p)
            d['Telephone'] = phone_numbers.get(customer.id, u'')
            result.append(d)
            community = communities.get(customer.community_id)  # type: Community
            d['Community'] = community.name if community else ''
            d['Language'] = customer.language

            for p, v in d.items():
                if v and isinstance(v, unicode):
                    d[p] = v.encode('utf-8')

    result.sort(key=lambda d: d['Language'])
    logging.debug('Creating csv with %s customers', len(result))
    fieldnames = ['name', 'Email', 'Customer since', 'address1', 'address2', 'zip_code', 'country', 'Telephone',
                  'App', 'Language']

    date = format_datetime(datetime.datetime.now(), locale='en_GB', format='medium')
    gcs_path = '/%s/customers/export-%s.csv' % (EXPORTS_BUCKET, date.replace(' ', '-'))
    with cloudstorage.open(gcs_path, 'w') as gcs_file:
        writer = csv.DictWriter(gcs_file, dialect='excel', fieldnames=fieldnames)
        writer.writeheader()
        for row in result:
            writer.writerow(row)

    current_date = format_date(datetime.date.today(), locale=DEFAULT_LANGUAGE)

    solution_server_settings = get_solution_server_settings()
    subject = 'Customers export %s' % current_date
    message = u'The exported customer list of %s can be found at %s' % (current_date, get_serving_url(gcs_path))

    send_mail(solution_server_settings.shop_export_email, [google_user.email()], subject, message)
    if DEBUG:
        with cloudstorage.open(gcs_path, 'r') as gcs_file:
            logging.info(gcs_file.read())


@returns(db.Query)
@arguments(app_id=unicode)
def get_all_customers_for_app(app_id):
    return Customer.all().filter('default_app_id =', app_id)


def export_cirklo_customers_csv(google_user, app_id):
    result = list()

    contact_data = {}
    qry = Contact.all()
    while True:
        contacts = qry.fetch(300)
        if not contacts:
            break
        for contact in contacts:
            contact_data[contact.customer_key.id()] = contact
        qry.with_cursor(qry.cursor())

    qry = get_all_customers_for_app(app_id)
    while True:
        customers = qry.fetch(300)
        if not customers:
            break
        logging.debug('Fetched %s customers', len(customers))
        qry.with_cursor(qry.cursor())
        for customer in customers:
            if customer.organization_type in (ServiceProfile.ORGANIZATION_TYPE_CITY, ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT):
                continue
            consents = get_customer_consents(customer.user_email)
            if SolutionServiceConsent.TYPE_CIRKLO_SHARE in consents.types:
                continue
            d = OrderedDict()
            d['Email'] = customer.user_email
            d['Name'] = customer.name
            d['creation_time'] = customer.creation_time
            d['Customer since'] = format_datetime(customer.creation_time, 'yyyy-MM-dd HH:mm:ss',
                                                  tzinfo=get_timezone('Europe/Brussels'))
            contact = contact_data.get(customer.id)
            d['First name'] = contact.first_name if contact else ''
            d['Last name'] = contact.last_name if contact else ''
            d['Link'] = get_customer_consent_cirklo_url(customer)
            result.append(d)
            for p, v in d.items():
                if v and isinstance(v, unicode):
                    d[p] = v.encode('utf-8')

    result.sort(key=lambda d: -d['creation_time'])
    logging.debug('Creating csv with %s customers', len(result))
    fieldnames = ['First name', 'Last name', 'Name', 'Email', 'Customer since', 'Link']

    date = format_datetime(datetime.datetime.now(), locale='en_GB', format='medium')
    gcs_path = '/%s/customers/export-cirklo-%s.csv' % (EXPORTS_BUCKET, date.replace(' ', '-'))
    with cloudstorage.open(gcs_path, 'w') as gcs_file:
        writer = csv.DictWriter(gcs_file, dialect='excel', fieldnames=fieldnames)
        writer.writeheader()
        for row in result:
            del row['creation_time']
            writer.writerow(row)

    current_date = format_date(datetime.date.today(), locale=DEFAULT_LANGUAGE)

    solution_server_settings = get_solution_server_settings()
    subject = 'Customers cirklo export %s' % current_date
    message = u'The exported customer list of %s can be found at %s' % (current_date, get_serving_url(gcs_path))

    send_mail(solution_server_settings.shop_export_email, [google_user.email()], subject, message)
    if DEBUG:
        with cloudstorage.open(gcs_path, 'r') as gcs_file:
            logging.info(gcs_file.read())


def create_customer_service_to(name, email, language, phone_number, organization_type, community_id, modules):
    # type: (str, str, str, str, int, str, List[str]) -> CustomerServiceTO
    service = CustomerServiceTO()
    service.name = name
    service.email = email and email.lower()
    service.language = language
    service.phone_number = phone_number

    service.organization_type = organization_type
    service.modules = modules
    service.managed_organization_types = []
    service.community_id = community_id

    validate_service(service)
    return service


def put_customer_with_service(service, name, address1, address2, zip_code, city, country, language,
                              organization_type, vat, customer_id=None,
                              website=None, facebook_page=None, force=False):
    # type: (CustomerServiceTO, str, str, str, str, str, str, str, str, str, int, str, str, bool) -> Tuple[Customer, bool, bool]

    def trans1():
        email_has_changed = False
        is_new = False
        customer = create_or_update_customer(customer_id=customer_id, vat=vat, name=name,
                                             address1=address1, address2=address2, zip_code=zip_code,
                                             country=country, language=language, city=city,
                                             organization_type=organization_type,
                                             force=force, website=website, facebook_page=facebook_page,
                                             community_id=service.community_id)

        customer.put()
        if customer_id:
            # Check if this city has access to this service
            if customer.community_id != service.community_id:
                logging.warn('Tried to save service information for service %s (%s)', customer.name, customer.community_id)
                raise NoPermissionException('Create association')

            # save the service.
            if service.email != customer.service_email:
                if service.email != customer.user_email:
                    email_has_changed = True

            update_contact(customer.id, Contact.get_one(customer.key()).id,
                           customer.name, u'', service.email, service.phone_number)
        else:
            is_new = True
            # create a new service. Name of the customer, contact, and service will all be the same.
            create_contact(customer, name, u'', service.email, service.phone_number)
        return customer, email_has_changed, is_new

    customer, email_changed, is_new_association = run_in_xg_transaction(trans1)
    return customer, email_changed, is_new_association


def get_signup_summary(lang, customer_signup):
    # type: (unicode, CustomerSignup) -> unicode
    """Get a translated signup summary."""

    def trans(term, *args, **kwargs):
        return common_translate(lang, unicode(term), *args, **kwargs)

    org_type = customer_signup.company_organization_type
    city_customer = customer_signup.city_customer
    community = get_community(city_customer.community_id)
    org_type_name = ServiceProfile.localized_singular_organization_type(org_type, lang, community.default_app)

    summary = u'{}\n\n'.format(trans('signup_application'))
    summary += u'{}\n'.format(trans('signup_inbox_message_header',
                                    name=customer_signup.company_name,
                                    org_type_name=org_type_name.lower()))

    summary += u'\n{}\n'.format(org_type_name)
    summary += u'{}: {}\n'.format(trans('organization_type'), org_type_name)
    summary += u'{}: {}\n'.format(trans('reservation-name'), customer_signup.company_name)
    summary += u'{}: {}\n'.format(trans('address'), customer_signup.company_address1)
    summary += u'{}: {}\n'.format(trans('zip_code'), customer_signup.company_zip_code)
    summary += u'{}: {}\n'.format(trans('Email'), customer_signup.company_email)
    summary += u'{}: {}\n'.format(trans('Phone number'), customer_signup.company_telephone)
    summary += u'{}: {}\n'.format(trans('city'), customer_signup.company_city)
    summary += u'{}: {}\n'.format(trans('vat'), customer_signup.company_vat)
    summary += u'{}: {}\n'.format(trans('Website'), customer_signup.company_website)
    summary += u'{}: {}\n'.format(trans('Facebook page'), customer_signup.company_facebook_page)

    summary += u'\n{}\n'.format(trans('business-manager'))
    summary += u'{}: {}\n'.format(trans('reservation-name'), customer_signup.customer_name)
    summary += u'{}: {}\n'.format(trans('address'), customer_signup.customer_address1)
    summary += u'{}: {}\n'.format(trans('zip_code'), customer_signup.customer_zip_code)
    summary += u'{}: {}\n'.format(trans('city'), customer_signup.customer_city)
    summary += u'{}: {}\n'.format(trans('Email'), customer_signup.customer_email)
    summary += u'{}: {}\n'.format(trans('Phone number'), customer_signup.customer_telephone)

    return summary


def _send_new_customer_signup_message(service_user, customer_signup):
    signup_key = unicode(customer_signup.key())
    sln_settings = get_solution_settings(service_user)
    summary = get_signup_summary(sln_settings.main_language, customer_signup)

    message = new_inbox_message(sln_settings, summary,
                                category=SolutionInboxMessage.CATEGORY_CUSTOMER_SIGNUP,
                                category_key=signup_key)

    app_user = None  # app user is not used when sending inbox forwarding msg that you can't reply to
    btn_accept = AnswerTO()
    btn_accept.id = u'approve'
    btn_accept.type = u'button'
    btn_accept.caption = common_translate(sln_settings.main_language, 'reservation-approve')
    btn_accept.ui_flags = 0
    btn_deny = AnswerTO()
    btn_deny.id = u'decline'
    btn_deny.type = u'button'
    btn_deny.caption = common_translate(sln_settings.main_language, 'reservation-decline')
    btn_deny.ui_flags = Message.UI_FLAG_EXPECT_NEXT_WAIT_5
    answers = [btn_accept, btn_deny]
    msg_params = {'if_name': customer_signup.customer_name, 'if_email': customer_signup.customer_email}
    send_inbox_forwarders_message(service_user, ServiceIdentity.DEFAULT, app_user, summary, msg_params,
                                  message_key=message.solution_inbox_message_key, reply_enabled=message.reply_enabled,
                                  answers=answers, flags=Message.FLAG_SHARED_MEMBERS)

    send_signup_update_messages(sln_settings, message)
    return message.solution_inbox_message_key


def calculate_customer_url_digest(data):
    alg = hashlib.sha256()
    alg.update(data['c'].encode('utf-8'))
    alg.update(data['s'].encode('utf-8'))
    return alg.hexdigest()


def send_signup_verification_email(city_customer, signup, host=None):
    # type: (Customer, CustomerSignup, str) -> None
    data = {'c': city_customer.service_user.email(), 's': unicode(signup.key()), 't': signup.timestamp}
    user = users.User(signup.customer_email)
    data['d'] = calculate_customer_url_digest(data)
    data = encrypt(user, json.dumps(data))
    url_params = urllib.urlencode({'email': signup.customer_email, 'data': base64.b64encode(data)})

    lang = city_customer.language
    translate = partial(common_translate, lang)
    base_url = host or get_server_settings().baseUrl
    link = '{}/customers/signup-password?{}'.format(base_url, url_params)
    subject = city_customer.name + ' - ' + translate('signup')
    params = {
        'language': lang,
        'name': signup.customer_name,
        'link_text': translate('verify'),
        'link': link
    }
    message = JINJA_ENVIRONMENT.get_template('emails/signup_verification.tmpl').render(params)
    html_message = JINJA_ENVIRONMENT.get_template('emails/signup_verification_html.tmpl').render(params)
    community = get_community(city_customer.community_id)
    app = get_app_by_id(community.default_app)
    from_email = "%s <%s>" % (community.name, app.dashboard_email_address)
    send_mail(from_email, signup.customer_email, subject, message, html=html_message)


@returns()
@arguments(city_customer_id=int, company=CompanyTO, customer=CustomerTO, recaptcha_token=unicode, domain=unicode,
           headers=dict)
def create_customer_signup(city_customer_id, company, customer, recaptcha_token, domain=None, headers=None):
    if not recaptcha_verify(recaptcha_token):
        raise HttpBadRequestException('Cannot verify recaptcha response')

    city_customer = Customer.get_by_id(city_customer_id)
    user_email = company.user_email.strip().lower()
    profile = get_service_or_user_profile(users.User(user_email))
    if isinstance(profile, ServiceProfile) or profile and profile.passwordHash:
        url = '{}/customers/signin?email={}'.format(get_server_url(), user_email)
        message = translate(customer.language, 'signup_already_registered_with_email')
        goto_login = translate(customer.language, 'go_to_login_page')
        raise HttpBadRequestException(message, {'url': url, 'label': goto_login})

    signup = CustomerSignup(parent=city_customer)

    signup.company_name = company.name
    signup.company_organization_type = company.organization_type or ServiceProfile.ORGANIZATION_TYPE_PROFIT
    signup.company_address1 = company.address1
    signup.company_zip_code = company.zip_code
    signup.company_city = company.city
    signup.company_email = user_email
    signup.company_telephone = company.telephone
    signup.company_website = company.website
    signup.company_facebook_page = company.facebook_page

    try:
        signup.company_vat = company.vat and normalize_vat(city_customer.country, company.vat)
    except BusinessException:
        msg = translate(customer.language, 'vat_invalid')
        raise HttpBadRequestException(msg)

    signup.customer_name = customer.name
    signup.customer_address1 = customer.address1
    signup.customer_zip_code = customer.zip_code
    signup.customer_city = customer.city
    signup.customer_email = customer.user_email.strip().lower()
    signup.customer_telephone = customer.telephone

    for other_signup in CustomerSignup.list_pending_by_customer_email(user_email):
        # check if the same information has been used in a pending signup
        if signup.is_same_signup(other_signup):
            message = shop_translate(customer.language, 'signup_same_information_used')
            raise HttpBadRequestException(message)

    signup.timestamp = now()
    signup.language = customer.language
    signup.put()
    send_signup_verification_email(city_customer, signup, domain)
    # Save accepted terms of use in a separate modal so we can save it to the ServiceProfile later
    tos_version = get_current_document_version(DOC_TERMS_SERVICE)
    customer_signup_ndb_key = ndb.Key(signup.kind(), signup.id, parent=ndb.Key(Customer.kind(), city_customer_id))
    key = LegalDocumentAcceptance.create_key(customer_signup_ndb_key, LegalDocumentType.TERMS_AND_CONDITIONS)
    LegalDocumentAcceptance(
        key=key,
        version=tos_version,
        headers=headers,
    ).put()


@returns(dict)
@arguments(email=unicode, data=unicode)
def validate_customer_url_data(email, data):
    try:
        user = users.User(email)
        data = base64.decodestring(data)
        data = json.loads(decrypt(user, data))
        azzert(data['d'] == calculate_customer_url_digest(data))
        return data
    except:
        raise InvalidUrlException


@returns()
@arguments(email=unicode, data=str, service_email=unicode)
def complete_customer_signup(email, data, service_email=None):
    @run_after_transaction
    def send_smart_emails(email, app_id):
        app_name = get_app_name_by_id(app_id)
        _schedule_signup_smart_emails(email, app_name)

    def update_signup():
        signup, parsed_data = get_customer_signup(email, data)
        service_user = users.User(parsed_data['c'])
        signup.inbox_message_key = _send_new_customer_signup_message(service_user, signup)
        signup.service_email = service_email
        signup.put()

        city_customer = signup.city_customer  # type: Customer
        if city_customer.language == 'nl':
            community = get_community(city_customer.community_id)
            send_smart_emails(signup.customer_email, community.default_app)

    run_in_xg_transaction(update_signup)


def get_customer_signup(email, data):
    parsed_data = validate_customer_url_data(email, data)
    signup = CustomerSignup.get(parsed_data['s'])
    if not signup:
        raise InvalidUrlException

    timestamp = signup.timestamp
    if not (timestamp < now() < timestamp + (3 * 24 * 3600)):
        raise ExpiredUrlException

    if signup.inbox_message_key:
        raise AlreadyUsedUrlException
    return signup, parsed_data


@returns(unicode)
@arguments(customer=Customer)
def get_customer_consent_cirklo_url(customer):
    if not customer.user_email:
        return ''

    url_params = urllib.urlencode({'cid': customer.id})
    host = get_server_settings().baseUrl
    return '{}/customers/consent/cirklo?{}'.format(host, url_params)


@returns(SolutionServiceConsent)
@arguments(email=unicode)
def get_customer_consents(email):
    # type: (unicode) -> SolutionServiceConsent
    key = SolutionServiceConsent.create_key(email)
    return key.get() or SolutionServiceConsent(key=key)


@returns()
@arguments(email=unicode, consents=dict, headers=dict, context=unicode)
def update_customer_consents(email, consents, headers, context):
    campaignmonitor_lists = {webhook.consent_type: webhook.list_id for webhook in CampaignMonitorWebhook.query()}
    for consent, granted in consents.iteritems():
        if consent in SolutionServiceConsent.EMAIL_CONSENT_TYPES:
            list_id = campaignmonitor_lists.get(consent)
            if not list_id:
                if DEBUG:
                    logging.error('No webhook configured for consent %s', consent)
                else:
                    raise Exception('No webhook configured for consent %s', consent)
        else:
            list_id = None
        data = {
            'context': context,
            'headers': headers,
            'date': datetime.datetime.now().isoformat() + 'Z'
        }
        if granted:
            # TODO: this is a crap solution that gets and puts the same model multiple times in this for loop
            add_service_consent(email, consent, data)
            if list_id:
                campaignmonitor.subscribe(list_id, email)
        else:
            remove_service_consent(email, consent, data)
            if list_id:
                campaignmonitor.unsubscribe(list_id, email)


@returns([tuple])
@arguments(customer=Customer, app_id=unicode, language=unicode, include_all=bool)
def get_organization_types(customer, app_id, language, include_all=False):
    # type: (Customer, unicode, unicode, bool) -> List[Tuple[int, unicode]]
    if not customer:
        return []
    if include_all:
        organization_types = [ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT, ServiceProfile.ORGANIZATION_TYPE_PROFIT,
                              ServiceProfile.ORGANIZATION_TYPE_CITY, ServiceProfile.ORGANIZATION_TYPE_EMERGENCY]
    else:
        organization_types = customer.editable_organization_types
    return [(org_type, ServiceProfile.localized_plural_organization_type(org_type, language, app_id))
            for org_type in organization_types]


def get_service_admins(service_user):
    qry = UserProfile.all(keys_only=True).filter('owningServiceEmails', service_user.email())
    return [key.name() for key in qry]


def add_service_admin(service_user, owner_user_email, base_url):
    # check existence
    service_email = service_user.email()
    service_profile = get_service_profile(service_user)

    user_profile = get_user_profile(users.User(owner_user_email), cached=False)
    password_hash = sha256_hex(unicode(generate_random_key()[:8]))
    if user_profile:
        logging.info('Coupling user %s to %s', owner_user_email, service_email)
        if service_email not in user_profile.owningServiceEmails:
            user_profile.owningServiceEmails.append(service_email)
        if not user_profile.passwordHash:
            user_profile.passwordHash = password_hash
            user_profile.isCreatedForService = True
        user_profile.put()
    else:
        logging.info('Coupling new user %s to %s', owner_user_email, service_email)
        service_identity = get_default_service_identity(service_user)
        user_profile = create_user_profile(users.User(owner_user_email), owner_user_email,
                                           service_profile.defaultLanguage) # todo communities set community_id
        user_profile.isCreatedForService = True
        user_profile.owningServiceEmails = [service_email]
        update_password_hash(user_profile, password_hash, now())
        action = common_translate(user_profile.language, 'reset-password')
        url_params = get_reset_password_url_params(user_profile.name, user_profile.user, action=action)
        reset_password_link = '%s/customers/setpassword?%s' % (base_url, url_params)
        params = {
            'service_name': service_identity.name,
            'user_email': owner_user_email,
            'user_name': user_profile.name,
            'link': reset_password_link,
            'link_text': common_translate(user_profile.language, 'set_password'),
            'language': service_profile.defaultLanguage
        }
        text_body = JINJA_ENVIRONMENT.get_template('emails/service_admin_added.tmpl').render(params)
        html_body = JINJA_ENVIRONMENT.get_template('emails/service_admin_added.html').render(params)
        subject = '%s - %s' % (common_translate(user_profile.language, 'our-city-app'),
                               common_translate(user_profile.language,
                                                'permission_granted_to_service'))
        app = get_app_by_id(user_profile.app_id)
        from_email = '%s <%s>' % (app.name, shop_translate(user_profile.language, 'oca_info_email_address'))
        send_mail(from_email, user_profile.user.email(), subject, text_body, html=html_body)


def import_customer(
    current_user, import_id, community_id, city_customer, currency, name, vat, org_type_name, email, phone,
    address, zip_code, city, website, facebook_page, contact_name, contact_address, contact_zipcode,
    contact_city, contact_email, contact_phone):
    def get_org_type(lang, name):
        translation_keys = {
            ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT: 'association',
            ServiceProfile.ORGANIZATION_TYPE_PROFIT: 'merchant',
            ServiceProfile.ORGANIZATION_TYPE_CITY: 'community_service',
            ServiceProfile.ORGANIZATION_TYPE_EMERGENCY: 'Care',
            ServiceProfile.ORGANIZATION_TYPE_UNSPECIFIED: 'service',
        }

        for org_type in ServiceProfile.ORGANIZATION_TYPES:
            translation_key = translation_keys.get(org_type)
            if name.lower() == localize(lang, translation_key).lower():
                return org_type

    try:
        language = city_customer.language
        org_type = get_org_type(language, org_type_name)
        email = email or contact_email
        address = address or contact_address
        phone = phone or contact_phone
        city = city or contact_city
        zip_code = zip_code or contact_zipcode
        modules = get_default_modules(city_customer)

        service = create_customer_service_to(name, email, language, phone, org_type, community_id, modules)

        customer, _, is_new_service = create_customer_with_service(
            city_customer, None, service, name, contact_address, '', contact_zipcode,
            contact_city, language, org_type, vat, website=website, facebook_page=facebook_page
        )

        first_name, _, last_name = contact_name.partition(' ')
        contact = Contact.get_one(customer.key())
        update_contact(
            customer.id, contact.id, first_name, last_name, contact_email, contact_phone)

        put_customer_service(
            customer, service, skip_module_check=True, search_enabled=False,
            skip_email_check=True, rollback=is_new_service)
        # TODO: save address & currency
    except:
        # TODO: show an error or send message cannot import customer
        logging.error(
            'Cannot create a service for imported customer %s (%s)', name, email, exc_info=True)
        channel.send_message(current_user, 'shop.customer.import.failed', import_id=import_id)
        return

    channel.send_message(current_user, 'shop.customer.import.success', import_id=import_id)
