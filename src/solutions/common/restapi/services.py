# -*- coding: utf-8 -*-  # Copyright 2017 Mobicage NV  #
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
# @@license_version:1.2@@

import logging
from types import NoneType

from google.appengine.ext import db
from mcfw.properties import azzert
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.models import ServiceProfile
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.service.api import system
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.to.messaging import KeyValueTO
from rogerthat.utils.channel import send_message
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import put_service, put_customer_with_service, audit_log, dict_str_for_audit_log
from shop.business.order import cancel_subscription
from shop.dal import get_customer
from shop.exceptions import DuplicateCustomerNameException
from shop.exceptions import NotOperatingInCountryException, EmptyValueException, InvalidEmailFormatException, \
    NoPermissionException, ServiceNameTooBigException
from shop.jobs.migrate_user import migrate as migrate_user
from shop.models import Customer, Contact, Product, RegioManagerTeam
from solutions import translate, SOLUTION_COMMON
from solutions.common.bizz import OrganizationType, SolutionModule, DEFAULT_BROADCAST_TYPES, ASSOCIATION_BROADCAST_TYPES
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionSettings
from solutions.common.to import ServiceTO
from solutions.common.to.qanda import ModuleTO
from solutions.common.to.services import ModuleAndBroadcastTypesTO, ServiceStatisticTO, ServicesTO, \
    ServiceListTO
from solutions.flex.bizz import get_services_statistics


def get_allowed_broadcast_types(city_customer):
    """
    Args:
        city_customer (Customer)
    """
    if city_customer.can_only_edit_organization_type(ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT):
        return ASSOCIATION_BROADCAST_TYPES
    else:
        return DEFAULT_BROADCAST_TYPES


def get_allowed_modules(city_customer):
    """
    Args:
        city_customer (Customer)
    """
    if city_customer.can_only_edit_organization_type(ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT):
        return SolutionModule.ASSOCIATION_MODULES
    else:
        return SolutionModule.POSSIBLE_MODULES


@rest("/common/services/get_defaults", "get", read_only_access=True)
@returns(ModuleAndBroadcastTypesTO)
@arguments()
def get_modules_and_broadcast_types():
    city_service_user = users.get_current_user()
    city_customer = get_customer(city_service_user)
    lang = get_solution_settings(city_service_user).main_language
    modules = [ModuleTO.fromArray([k, SolutionModule.get_translated_description(lang, k)]) for k in
               get_allowed_modules(city_customer)]
    broadcast_types = [translate(lang, SOLUTION_COMMON, k) for k in get_allowed_broadcast_types(city_customer)]
    organization_types = [KeyValueTO(unicode(t), ServiceProfile.localized_singular_organization_type(t, lang))
                          for t in city_customer.editable_organization_types]
    return ModuleAndBroadcastTypesTO(modules, broadcast_types, organization_types)


@rest("/common/services/get_all", "get", read_only_access=True)
@returns(ServicesTO)
@arguments()
def get_services():
    city_service_user = users.get_current_user()
    si = system.get_identity()
    # get all the services in this city
    app_id = si.app_ids[0]
    city_customer = get_customer(city_service_user)
    if len(city_customer.editable_organization_types) == 1:
        organization_type = city_customer.editable_organization_types[0]
        service_customers = list(Customer.list_enabled_by_organization_type_in_app(app_id, organization_type))
    else:
        service_customers = list(Customer.list_enabled_by_app(app_id))
    services = []
    statistics = get_services_statistics(app_id)
    sln_settings_keys = [SolutionSettings.create_key(city_service_user)]
    for customer in service_customers:
        if not customer.service_email:
            logging.error('Customer %d (%s) has default_app_id, but has no service!', customer.id, customer.name)
        elif customer.app_id == app_id:
            sln_settings_keys.append(SolutionSettings.create_key(users.User(customer.service_email)))
    sln_settings_list = db.get(sln_settings_keys)
    sln_settings = sln_settings_list.pop(0)  # type: SolutionSettings
    azzert(SolutionModule.CITY_APP in sln_settings.modules)
    for customer in service_customers:
        service_email = customer.service_email
        # Exclude the city app's own service
        if customer.app_id == app_id and service_email != sln_settings.service_user.email():
            future_events_count = 0
            broadcasts_last_month = 0
            static_content_count = 0
            last_unanswered_question_timestamp = 0
            modules = []
            for sln_settings in sln_settings_list:
                if sln_settings.key().name() == service_email:
                    modules = sln_settings.modules
            if statistics:
                for mail in statistics.customer_emails:
                    if mail == service_email:
                        index = statistics.customer_emails.index(mail)
                        future_events_count = statistics.future_events_count[index]
                        broadcasts_last_month = statistics.broadcasts_last_month[index]
                        static_content_count = statistics.static_content_count[index]
                        last_unanswered_question_timestamp = statistics.last_unanswered_questions_timestamps[index]

            statistic = ServiceStatisticTO.create(future_events_count, broadcasts_last_month, static_content_count,
                                                  last_unanswered_question_timestamp)
            services.append(ServiceListTO(service_email, customer.name, statistic, modules))
    generated_on = statistics.generated_on if statistics else None
    return ServicesTO(sorted(services, key=lambda x: x.name.lower()), generated_on)


@rest("/common/services/get", "get", read_only_access=True)
@returns(ServiceTO)
@arguments(service_email=unicode)
def get_service(service_email):
    city_service_user = users.get_current_user()
    city_customer = get_customer(city_service_user)
    service_user = users.User(email=service_email)
    customer = Customer.get_by_service_email(service_email)
    if city_customer.organization_type != OrganizationType.CITY or (
                customer and customer.organization_type not in city_customer.editable_organization_types):
        logging.warn(u'Service %s tried to save service information for customer %d', city_service_user, customer.id)
        lang = get_solution_settings(city_service_user).main_language
        return ReturnStatusTO.create(False, translate(lang, SOLUTION_COMMON, 'no_permission'))
    contact = Contact.get_one(customer.key())
    solution_settings = get_solution_settings(service_user)
    return ServiceTO(customer.id, customer.name, customer.address1, customer.address2, customer.zip_code, customer.city,
                     customer.user_email, contact.phone_number, solution_settings.main_language,
                     solution_settings.modules, solution_settings.broadcast_types, customer.organization_type,
                     customer.vat)


@rest("/common/services/put", "post", read_only_access=False)
@returns(ReturnStatusTO)
@arguments(name=unicode, address1=unicode, address2=unicode, zip_code=unicode, city=unicode, user_email=unicode,
           telephone=unicode, language=unicode, modules=[unicode], broadcast_types=[unicode],
           customer_id=(int, long, NoneType), organization_type=(int, long), vat=unicode)
def rest_put_service(name, address1, address2, zip_code, city, user_email, telephone, language, modules,
                     broadcast_types, customer_id=None, organization_type=OrganizationType.PROFIT, vat=None):
    city_service_user = users.get_current_user()
    city_customer = get_customer(city_service_user)
    city_sln_settings = get_solution_settings(city_service_user)
    lang = city_sln_settings.main_language
    customer_key = None
    customer = Customer.get_by_id(customer_id) if customer_id else None
    # check if the current user is in fact a city app
    if city_customer.organization_type != OrganizationType.CITY or (
                customer and customer.organization_type not in city_customer.editable_organization_types):
        logging.warn(u'Service {} tried to save service information for customer {}'.format(city_service_user, customer_id))
        return ReturnStatusTO.create(False, translate(lang, SOLUTION_COMMON, 'no_permission'))
    if not customer and organization_type not in city_customer.editable_organization_types:
        organization_type = city_customer.editable_organization_types[0]
    success1 = False
    error_msg = None
    email_changed = False
    is_new_service = False

    mods = [m for m in SolutionModule.MANDATORY_MODULES]
    mods.extend([m for m in modules if m in get_allowed_modules(city_customer)])
    modules = list(set(mods))

    if SolutionModule.BROADCAST in modules and not broadcast_types:
        modules.remove(SolutionModule.BROADCAST)

    try:
        if city_customer.can_only_edit_organization_type(ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT):
            product_code = Product.PRODUCT_SUBSCRIPTION_ASSOCIATION
        else:
            product_code = Product.PRODUCT_FREE_SUBSCRIPTION

        team = RegioManagerTeam.get_by_id(city_customer.team_id)
        if not team.legal_entity.is_mobicage:
            if product_code == Product.PRODUCT_SUBSCRIPTION_ASSOCIATION:
                from shop.products import create_sjup_product
                p = create_sjup_product(team.legal_entity_id, "%s." % team.legal_entity_id)
                p.put()
                product_code = p.code
            else:
                from shop.products import create_free_product
                p = create_free_product(team.legal_entity_id, "%s." % team.legal_entity_id)
                p.put()
                product_code = p.code

        (customer, service, email_changed, is_new_service) \
 = put_customer_with_service(name, address1, address2, zip_code, city, user_email, telephone, language,
                                        modules, broadcast_types, organization_type, city_customer.app_id,
                                        city_sln_settings.currency, city_customer.country, city_customer.team_id,
                                        product_code, customer_id, vat)
        customer_key = customer.key()
        success1 = True
    except EmptyValueException as ex:
        val_name = translate(lang, SOLUTION_COMMON, ex.value_name)
        error_msg = translate(lang, SOLUTION_COMMON, 'empty_field_error', field_name=val_name)
    except ServiceNameTooBigException:
        error_msg = translate(lang, SOLUTION_COMMON, 'name_cannot_be_bigger_than_n_characters', n=50)
    except DuplicateCustomerNameException as ex:
        error_msg = translate(lang, SOLUTION_COMMON, 'duplicate_customer', customer_name=ex.name)
    except NoPermissionException:
        error_msg = translate(lang, SOLUTION_COMMON, 'no_permission')
    except InvalidEmailFormatException as ex:
        error_msg = translate(lang, SOLUTION_COMMON, 'invalid_email_format', email=ex.email)
    except NotOperatingInCountryException as ex:
        error_msg = translate(lang, SOLUTION_COMMON, 'not_operating_in_country', country=ex.country)
    except BusinessException as ex:
        logging.debug('Failed to create service, BusinessException', exc_info=True)
        error_msg = ex.message
    except:
        logging.exception('Failed to create service')
        error_msg = translate(lang, SOLUTION_COMMON, 'failed_to_create_service')
    finally:
        if not success1:
            return ReturnStatusTO.create(False, error_msg)

    def trans2():
        # create/update service
        put_service(customer, service, skip_module_check=True, search_enabled=False, skip_email_check=True)

    success2 = False
    try:
        run_in_xg_transaction(trans2)
        success2 = True
    except EmptyValueException as ex:
        val_name = translate(lang, SOLUTION_COMMON, ex.value_name)
        error_msg = translate(lang, SOLUTION_COMMON, 'empty_field_error', field_name=val_name)
    except:
        logging.exception('Could not save service service information')
        error_msg = translate(lang, SOLUTION_COMMON, 'failed_to_create_service')
    finally:
        if not success2:
            if is_new_service:
                logging.warn('Failed to save new service service information, reverting changes...')
                db.delete(db.GqlQuery("SELECT __key__ WHERE ANCESTOR IS KEY('%s')" % customer_key).fetch(None))
            return ReturnStatusTO.create(False, error_msg)
        else:
            if email_changed:
                migrate_user(users.User(customer.user_email), users.User(customer.user_email), users.User(user_email),
                             customer.service_email)
                customer.user_email = user_email
                customer.put()
            variables = dict_str_for_audit_log({
                'user_email': user_email,
                'modules': modules,
            })
            audit_log(customer_id, 'put_service', variables, city_service_user)
            return RETURNSTATUS_TO_SUCCESS


@rest('/common/services/delete', 'post', read_only_access=False)
@returns(ReturnStatusTO)
@arguments(service_email=unicode)
def rest_delete_service(service_email):
    city_service_user = users.get_current_user()
    city_customer = get_customer(city_service_user)
    customer = Customer.get_by_service_email(service_email)
    if city_customer.organization_type != OrganizationType.CITY \
            or customer.organization_type not in city_customer.editable_organization_types:
        lang = get_solution_settings(city_service_user).main_language
        logging.warn(u'Service %s tried to save service information for customer %d', city_service_user, customer.id)
        return ReturnStatusTO.create(False, translate(lang, SOLUTION_COMMON, 'no_permission'))
    cancel_subscription(customer.id, Customer.DISABLED_REASONS[Customer.DISABLED_ASSOCIATION_BY_CITY], True)
    send_message(users.get_current_user(),
                 [{u"type": u"solutions.common.services.deleted", u'service_email': service_email}])
    return RETURNSTATUS_TO_SUCCESS
