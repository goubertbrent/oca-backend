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
import logging
from collections import OrderedDict
from datetime import datetime
from types import NoneType

import cloudstorage
import xlwt
from babel.dates import format_datetime
from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred
from typing import List

from mcfw.exceptions import HttpForbiddenException
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.communities.models import Community
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.bizz.maps.services.places import get_place_types
from rogerthat.consts import EXPORTS_BUCKET, SCHEDULED_QUEUE
from rogerthat.dal.profile import get_service_profile
from rogerthat.models import ServiceIdentity, ServiceProfile
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS, \
    WarningReturnStatusTO
from rogerthat.utils.channel import send_message_to_session
from shop.bizz import create_customer_service_to, search_customer, \
    update_contact
from shop.business.order import cancel_subscription
from shop.dal import get_customer
from shop.exceptions import DuplicateCustomerNameException, NotOperatingInCountryException, EmptyValueException, \
    InvalidEmailFormatException, NoPermissionException, ServiceNameTooBigException
from shop.jobs.migrate_user import migrate as migrate_user
from shop.models import Customer, Contact, LegalDocumentAcceptance, LegalDocumentType, CustomerSignup
from shop.to import CustomerTO
from solutions import translate
from solutions.common.bizz import OrganizationType, common_provision
from solutions.common.bizz.service import create_customer_with_service, filter_modules, put_customer_service, \
    set_customer_signup_status, get_default_modules
from solutions.common.dal import get_solution_settings
from solutions.common.to import ServiceTO
from solutions.common.to.services import ServicesTO, ServiceListTO


@rest('/common/services/search', 'post')
@returns([CustomerTO])
@arguments(search_string=unicode, organization_type=(NoneType, int))
def search_services(search_string, organization_type=None):
    city_service_user = users.get_current_user()
    community = _check_is_city(city_service_user)

    customers = []
    # if app id is set, the customer should have a service
    for c in search_customer(search_string, [community.id], organization_type=organization_type):
        # exclude own service and disabled services
        if c.service_email == city_service_user.email() or c.service_disabled_at:
            continue
        customers.append(CustomerTO.fromCustomerModel(c))

    return customers


@rest('/common/services/get_all', 'get', read_only_access=True)
@returns(ServicesTO)
@arguments(organization_type=int, cursor=unicode, limit=int)
def get_services(organization_type, cursor=None, limit=50):
    city_service_user = users.get_current_user()
    community = _check_is_city(city_service_user)
    # get all the services in this community
    service_customers_qry = Customer.list_enabled_by_organization_type_in_community(community.id, organization_type)
    service_customers_qry.with_cursor(cursor)
    service_customers = service_customers_qry.fetch(limit)
    new_cursor = unicode(service_customers_qry.cursor())
    services = []
    city_service_email = city_service_user.email()
    for customer in service_customers:
        service_email = customer.service_email
        # Exclude the city app's own service
        if service_email == city_service_email:
            continue
        services.append(ServiceListTO(service_email, customer.name, customer.id))
    return ServicesTO(sorted(services, key=lambda x: x.name.lower()), new_cursor)


def _check_is_city(city_service_user, customer=None):
    # type: (users.User, Customer) -> Community
    community_id = get_service_profile(city_service_user).community_id
    community = get_community(community_id)
    # Check if the customer his community is the same as the city that's trying to edit it
    if not community.can_edit_services(city_service_user) or (customer and customer.community_id != community_id):
        raise HttpForbiddenException()
    return community


@rest('/common/services/export', 'get', read_only_access=False)
@returns(dict)
@arguments()
def rest_export_services():
    city_service_user = users.get_current_user()
    city_sln_settings = get_solution_settings(city_service_user)
    community = _check_is_city(city_service_user)

    customers = [c for c in Customer.list_by_community_id(community.id)
                 if not c.service_disabled_at]  # type: List[Customer]
    service_infos = {s.service_user: s for s in ndb.get_multi([
        ServiceInfo.create_key(customer.service_user, ServiceIdentity.DEFAULT)
        for customer in customers if customer.service_email])
                     }
    result = []
    language = city_sln_settings.main_language
    place_types = get_place_types(language)
    name_field = translate(language, 'reservation-name')

    email = translate(language, 'Email')
    phone_number = translate(language, 'Phone number')
    service_created = translate(language, 'creation_date')
    address = translate(language, 'address')
    place_type = translate(language, 'oca.place_type')
    organization_type = translate(language, 'organization_type')

    excel_date_format = xlwt.XFStyle()
    excel_date_format.num_format_str = 'dd/mm/yyyy'
    row_style = {
        service_created: excel_date_format,
    }

    from rogerthat.translations import localize
    org_types = {
            ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT: localize(language, 'Associations'),
            ServiceProfile.ORGANIZATION_TYPE_PROFIT: localize(language, 'Merchants'),
            ServiceProfile.ORGANIZATION_TYPE_CITY: localize(language, 'Community Services'),
            ServiceProfile.ORGANIZATION_TYPE_EMERGENCY: localize(language, 'Care'),
            ServiceProfile.ORGANIZATION_TYPE_UNSPECIFIED: localize(language, 'Services'),
        }

    for customer in customers:
        service_info = service_infos.get(customer.service_user) or ServiceInfo()  # type: ServiceInfo
        d = OrderedDict()
        d[name_field] = service_info.name or customer.name
        d[email] = customer.user_email
        d[phone_number] = service_info.main_phone_number or ''
        d[service_created] = datetime.utcfromtimestamp(customer.creation_time)
        d[address] = service_info.main_address(city_sln_settings.locale) or ''
        d[place_type] = place_types.get(service_info.main_place_type) or ''
        d[organization_type] = org_types.get(customer.organization_type)
        result.append(d)

    result.sort(key=lambda d: d[name_field])

    date = format_datetime(datetime.now(), locale=city_sln_settings.locale, format='medium')
    gcs_path = '/%s/customers/%d/export-%s.xls' % (EXPORTS_BUCKET, community.id, date.replace(' ', '-'))
    with cloudstorage.open(gcs_path, 'w') as gcs_file:
        book = xlwt.Workbook(encoding='utf-8')
        sheet = book.add_sheet(translate(language, 'services'))  # type: xlwt.Worksheet
        columns = result[0].keys()
        for column_index, column_name in enumerate(columns):
            sheet.write(0, column_index, column_name)
        for row_number, row in enumerate(result):
            for column_index, column_name in enumerate(columns):
                sheet.write(row_number + 1, column_index, row[column_name], row_style.get(column_name, xlwt.Style.default_style))
        book.save(gcs_file)

    deferred.defer(cloudstorage.delete, gcs_path, _countdown=86400, _queue=SCHEDULED_QUEUE)
    return {
        'url': get_serving_url(gcs_path)
    }


@rest('/common/services/get', 'get', read_only_access=True)
@returns((ServiceTO, ReturnStatusTO))
@arguments(service_email=unicode)
def get_service(service_email):
    city_service_user = users.get_current_user()
    service_user = users.User(email=service_email)
    customer = get_customer(users.User(service_email))  # type: Customer
    _check_is_city(city_service_user, customer)
    contact = Contact.get_one(customer.key())  # type: Contact
    solution_settings = get_solution_settings(service_user)
    return ServiceTO(customer.id, customer.name, customer.address1, customer.address2, customer.zip_code, customer.city,
                     customer.user_email, contact.phone_number, solution_settings.main_language,
                     solution_settings.modules, customer.organization_type,
                     customer.vat, customer.website, customer.facebook_page, solution_settings.hidden_by_city)


@rest('/common/services/set-visibility', 'post')
@returns()
@arguments(customer_id=(int, long), visible=bool)
def rest_set_service_visibility(customer_id, visible):
    city_service_user = users.get_current_user()
    customer = Customer.get_by_id(customer_id)  # type: Customer
    _check_is_city(city_service_user, customer)
    sln_settings = get_solution_settings(customer.service_user)
    sln_settings.hidden_by_city = None if visible else datetime.now()
    sln_settings.updates_pending = True
    sln_settings.put()
    common_provision(sln_settings.service_user)


@rest("/common/services/put", "post", read_only_access=False)
@returns(WarningReturnStatusTO)
@arguments(name=unicode, address1=unicode, address2=unicode, zip_code=unicode, city=unicode, user_email=unicode,
           telephone=unicode, language=unicode, customer_id=(int, long, NoneType), organization_type=(int, long),
           vat=unicode, modules=[unicode], website=unicode, facebook_page=unicode, force=bool)
def rest_put_service(name, address1, address2, zip_code, city, user_email, telephone, language,
                     customer_id=None, organization_type=OrganizationType.PROFIT, vat=None,
                     modules=None, website=None, facebook_page=None, force=False):
    city_service_user = users.get_current_user()
    city_customer = get_customer(city_service_user)
    city_sln_settings = get_solution_settings(city_service_user)
    lang = city_sln_settings.main_language
    customer = Customer.get_by_id(customer_id) if customer_id else None
    community = _check_is_city(city_service_user, customer)

    error_msg = warning_msg = None
    email_changed = False
    is_new_service = False

    try:
        if not modules:
            modules = filter_modules(city_customer, get_default_modules(city_customer))

        service = create_customer_service_to(name, user_email, language, telephone, organization_type,
                                             community.id, modules)
        (customer, email_changed, is_new_service) \
            = create_customer_with_service(city_customer, customer, service, name, address1, address2, zip_code, city,
                                           language, organization_type, vat, website, facebook_page, force=force)
    except EmptyValueException as ex:
        val_name = translate(lang, ex.value_name)
        error_msg = translate(lang, 'empty_field_error', field_name=val_name)
    except ServiceNameTooBigException:
        error_msg = translate(lang, 'name_cannot_be_bigger_than_n_characters', n=50)
    except DuplicateCustomerNameException as ex:
        warning_msg = translate(lang, 'duplicate_customer', customer_name=ex.name)
    except NoPermissionException:
        error_msg = translate(lang, 'no_permission')
    except InvalidEmailFormatException as ex:
        error_msg = translate(lang, 'invalid_email_format', email=ex.email)
    except NotOperatingInCountryException as ex:
        error_msg = translate(lang, 'not_operating_in_country', country=ex.country)
    except BusinessException as ex:
        logging.debug('Failed to create service, BusinessException', exc_info=True)
        error_msg = ex.message
    except:
        logging.exception('Failed to create service')
        error_msg = translate(lang, 'failed_to_create_service')
    finally:
        if error_msg:
            return WarningReturnStatusTO.create(False, error_msg)
        elif warning_msg:
            return WarningReturnStatusTO.create(False, warningmsg=warning_msg)

    try:
        put_customer_service(customer, service, skip_module_check=True, search_enabled=False,
                             skip_email_check=True, rollback=is_new_service)
    except EmptyValueException as ex:
        val_name = translate(lang, ex.value_name)
        error_msg = translate(lang, 'empty_field_error', field_name=val_name)
    except:
        logging.exception('Could not save service service information')
        error_msg = translate(lang, 'failed_to_create_service')
    finally:
        if error_msg:
            if is_new_service:
                logging.warn('Failed to save new service service information, changes would be reverted...')
            return WarningReturnStatusTO.create(False, error_msg)
        else:
            if email_changed:
                migrate_user(users.User(customer.user_email), users.User(customer.user_email), users.User(user_email),
                             customer.service_email)
                customer.user_email = user_email
                customer.put()
            return WarningReturnStatusTO.create()


@rest('/common/services/delete', 'post', read_only_access=False)
@returns(ReturnStatusTO)
@arguments(service_email=unicode)
def rest_delete_service(service_email):
    city_service_user = users.get_current_user()
    customer = Customer.get_by_service_email(service_email)
    _check_is_city(city_service_user, customer)
    if service_email == city_service_user.email():
        logging.warn(u'Service %s tried to delete its own service', city_service_user)
        lang = get_solution_settings(city_service_user).main_language
        return ReturnStatusTO.create(False, translate(lang, 'no_permission'))
    cancel_subscription(customer.id, Customer.DISABLED_REASONS[Customer.DISABLED_BY_CITY])
    session = users.get_current_session()
    service_identity = session.service_identity
    send_message_to_session(city_service_user, session,
                            [{u"type": u"solutions.common.services.deleted",
                              u'service_email': service_email,
                              u'service_organization_type': customer.organization_type}],
                            si=service_identity)
    return RETURNSTATUS_TO_SUCCESS


def _fill_signup_data(signup, *prop_names):
    """Old signups may have data stored in customer_<prop_name> instead of company_<prop-name>"""
    for prop_name in prop_names:
        company_prop_name = 'company_' + prop_name
        current_value = getattr(signup, company_prop_name)
        if not current_value:
            setattr(signup, company_prop_name, getattr(signup, 'customer_' + prop_name))


def _update_signup_contact(customer, signup):
    contact = Contact.get_one(customer.key())
    first_name, _, last_name = signup.customer_name.partition(' ')
    update_contact(customer.id, contact.id, first_name, last_name, signup.customer_email,
                   signup.customer_telephone)


@rest('/common/signup/services/create', 'post', read_only_access=False)
@returns(WarningReturnStatusTO)
@arguments(signup_key=unicode, force=bool)
def rest_create_service_from_signup(signup_key, force=False):
    signup = db.get(signup_key)  # type: CustomerSignup
    if signup.done or not signup.can_update:
        return WarningReturnStatusTO.create(success=True)

    city_service_user = users.get_current_user()
    city_customer = get_customer(city_service_user)
    city_sln_settings = get_solution_settings(city_service_user)
    city_language = city_sln_settings.main_language
    _check_is_city(city_service_user)
    if not signup:
        return WarningReturnStatusTO.create(False, translate(city_language, 'signup_not_found'))
    has_service = signup.service_email is not None
    if not has_service:
        result = do_create_service(city_customer, city_language, force, signup, password=None)
    else:
        result = WarningReturnStatusTO.create(True)
    if result.success:
        set_customer_signup_status(city_customer, signup, approved=True, send_approval_email=not has_service)
    return result


def do_create_service(city_customer, language, force, signup, password, tos_version=None):
    error_msg = warning_msg = None
    try:
        modules = CustomerSignup.DEFAULT_MODULES
        _fill_signup_data(signup, 'email', 'telephone', 'website', 'facebook_page')
        modules = filter_modules(city_customer, modules)

        service = create_customer_service_to(signup.company_name, signup.company_email, signup.language,
                                             signup.company_telephone, signup.company_organization_type,
                                             city_customer.community_id, modules)

        customer = create_customer_with_service(
            city_customer, None, service, signup.company_name,
            signup.customer_address1, None, signup.company_zip_code,
            signup.company_city, signup.language, signup.company_organization_type,
            signup.company_vat, signup.company_website, signup.company_facebook_page, force=force)[0]

        # update the contact, as it should be created by now
        _update_signup_contact(customer, signup)

    except EmptyValueException as ex:
        val_name = translate(language, ex.value_name)
        error_msg = translate(language, 'empty_field_error', field_name=val_name)
    except ServiceNameTooBigException:
        error_msg = translate(language, 'name_cannot_be_bigger_than_n_characters', n=50)
    except DuplicateCustomerNameException as ex:
        warning_msg = translate(language, 'duplicate_customer', customer_name=ex.name)
    except NoPermissionException:
        error_msg = translate(language, 'no_permission')
    except InvalidEmailFormatException as ex:
        error_msg = translate(language, 'invalid_email_format', email=ex.email)
    except NotOperatingInCountryException as ex:
        error_msg = translate(language, 'not_operating_in_country', country=ex.country)
    except BusinessException as ex:
        logging.debug('Failed to create service, BusinessException', exc_info=True)
        error_msg = ex.message
    except:
        logging.exception('Failed to create service')
        error_msg = translate(language, 'failed_to_create_service')
    finally:
        if error_msg:
            return WarningReturnStatusTO.create(False, error_msg)
        elif warning_msg:
            return WarningReturnStatusTO.create(False, warningmsg=warning_msg)
        else:
            try:
                result = put_customer_service(customer, service, skip_module_check=True, search_enabled=False,
                                              skip_email_check=True, rollback=True, password=password,
                                              tos_version=tos_version)
                if not tos_version:
                    deferred.defer(copy_accepted_terms_of_use, signup.key(), users.User(result.login), _countdown=5)
                logging.debug('Service created from signup: %s, with modules of %s', signup.key(), modules)
                return WarningReturnStatusTO.create(success=True, data={'service_email': result.login})
            except EmptyValueException as ex:
                val_name = translate(language, ex.value_name)
                error_msg = translate(language, 'empty_field_error', field_name=val_name)
            except:
                logging.exception('Could not save service information')
                error_msg = translate(language, 'failed_to_create_service')
            finally:
                if error_msg:
                    return WarningReturnStatusTO.create(False, error_msg)


def copy_accepted_terms_of_use(signup_key, service_user):
    # type: (db.Key, users.User) -> None
    original_key = LegalDocumentAcceptance.create_key(ndb.Key.from_old_key(signup_key),  # @UndefinedVariable
                                                      LegalDocumentType.TERMS_AND_CONDITIONS)
    doc = original_key.get()  # type: LegalDocumentAcceptance
    if doc:
        service_profile = get_service_profile(service_user)
        logging.debug('Copying accepted terms of use to service profile: %s -> %s', original_key, service_profile.key())
        service_profile.tos_version = doc.version
        service_profile.put()
