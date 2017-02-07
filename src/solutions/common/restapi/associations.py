# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

import logging
from types import NoneType

from google.appengine.ext import db

from mcfw.properties import azzert
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.service.api import system
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.utils.channel import send_message
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import put_service, put_customer_with_service
from shop.business.order import cancel_subscription
from shop.dal import get_customer
from shop.exceptions import DuplicateCustomerNameException
from shop.exceptions import NotOperatingInCountryException, EmptyValueException, InvalidEmailFormatException, \
    NoPermissionException
from shop.jobs.migrate_user import migrate as migrate_user
from shop.models import Customer, Contact, Product
from solutions import translate, SOLUTION_COMMON
from solutions.common.bizz import OrganizationType, SolutionModule, ASSOCIATION_BROADCAST_TYPES
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionSettings
from solutions.common.to import AssociationTO
from solutions.common.to.associations import ModuleAndBroadcastTypesTO, AssociationStatisticTO, AssociationsTO, \
    ServiceTO
from solutions.common.to.qanda import ModuleTO
from solutions.flex.bizz import get_associations_statistics


@rest("/common/associations/get_defaults", "get", read_only_access=True)
@returns(ModuleAndBroadcastTypesTO)
@arguments()
def get_modules_and_broadcast_types():
    service_user = users.get_current_user()
    lang = get_solution_settings(service_user).main_language
    modules = [ModuleTO.fromArray([k, SolutionModule.get_translated_description(lang, k)]) for k in
               SolutionModule.ASSOCIATION_MODULES]
    broadcast_types = [translate(lang, SOLUTION_COMMON, k) for k in ASSOCIATION_BROADCAST_TYPES]
    return ModuleAndBroadcastTypesTO.create(modules, broadcast_types)


@rest("/common/associations/get_all", "get", read_only_access=True)
@returns(AssociationsTO)
@arguments()
def get_associations():
    si = system.get_identity()
    # get all the associations in this city
    app_id = si.app_ids[0]
    association_customers = list(Customer.get_all_associations_in_app(app_id))
    associations = list()
    statistics = get_associations_statistics(app_id)
    sln_settings_keys = [SolutionSettings.create_key(users.get_current_user())]
    for asso in association_customers:
        if not asso.service_email:
            logging.error('Association %s has app_ids, but has no service!', asso.name)
        elif asso.app_id == app_id:
            sln_settings_keys.append(
                SolutionSettings.create_key(users.User(asso.service_email))
            )
    sln_settings_list = db.get(sln_settings_keys)
    sln_settings = sln_settings_list.pop(0)
    azzert(SolutionModule.CITY_APP in sln_settings.modules)
    for asso in association_customers:
        if asso.app_id == app_id:
            service_email = asso.service_email
            future_events_count = 0
            broadcasts_last_month = 0
            static_content_count = 0
            last_unanswered_question_timestamp = 0
            modules = list()
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

            statistic = AssociationStatisticTO.create(future_events_count, broadcasts_last_month, static_content_count,
                                                      last_unanswered_question_timestamp)
            associations.append(ServiceTO.create(service_email, asso.name, statistic, modules))
    generated_on = statistics.generated_on if statistics else None
    return AssociationsTO.create(sorted(associations, key=lambda x: x.name.lower()), generated_on)


@rest("/common/associations/get", "get", read_only_access=True)
@returns(AssociationTO)
@arguments(service_email=unicode)
def get_association(service_email):
    city_service_user = users.get_current_user()
    city_customer = get_customer(city_service_user)
    if not city_customer.organization_type == OrganizationType.CITY:
        logging.warn(u'Customer %s tried to get service information for service' % service_email)
        return
    association = Customer.get_by_service_email(service_email)
    contact = Contact.get_one(association.key())
    service_user = users.User(email=service_email)
    solution_settings = get_solution_settings(service_user)
    return AssociationTO.create(association.id, association.name, association.address1, association.address2,
                                association.zip_code, association.city, association.user_email, contact.phone_number,
                                solution_settings.main_language, solution_settings.modules,
                                solution_settings.broadcast_types)


@rest("/common/associations/put", "post", read_only_access=False)
@returns(ReturnStatusTO)
@arguments(name=unicode, address1=unicode, address2=unicode, zip_code=unicode,
           city=unicode, user_email=unicode, telephone=unicode, language=unicode, modules=[unicode],
           broadcast_types=[unicode], customer_id=(int, long, NoneType))
def put_association(name, address1, address2, zip_code, city, user_email, telephone, language, modules,
                    broadcast_types, customer_id=None):
    city_service_user = users.get_current_user()
    city_customer = get_customer(city_service_user)
    city_sln_settings = get_solution_settings(city_service_user)
    lang = city_sln_settings.main_language
    customer_key = None
    customer = None
    # check if the current user is in fact a city app
    if not city_customer.organization_type == OrganizationType.CITY:
        logging.warn(u'Customer %s tried to save service information for service' % customer_id)
        return ReturnStatusTO.create(False, translate(lang, SOLUTION_COMMON, 'no_permission'))
    success1 = False
    error_msg = None
    email_changed = False
    is_new_association = False

    mods = [m for m in SolutionModule.ASSOCIATION_MANDATORY_MODULES]
    mods.extend([m for m in modules if m in SolutionModule.ASSOCIATION_MODULES])
    modules = list(set(mods))

    try:
        (customer, service, email_changed, is_new_association) \
            = put_customer_with_service(name, address1, address2, zip_code, city, user_email, telephone, language,
                                        modules, broadcast_types, OrganizationType.NON_PROFIT, city_customer.app_id,
                                        city_sln_settings.currency, city_customer.country, city_customer.team_id,
                                        Product.PRODUCT_SUBSCRIPTION_ASSOCIATION, customer_id)
        customer_key = customer.key()
        success1 = True
    except EmptyValueException, ex:
        val_name = translate(lang, SOLUTION_COMMON, ex.value_name)
        error_msg = translate(lang, SOLUTION_COMMON, 'empty_field_error', field_name=val_name)
    except DuplicateCustomerNameException, ex:
        error_msg = translate(lang, SOLUTION_COMMON, 'duplicate_customer', customer_name=ex.name)
    except NoPermissionException:
        error_msg = translate(lang, SOLUTION_COMMON, 'no_permission')
    except InvalidEmailFormatException, ex:
        error_msg = translate(lang, SOLUTION_COMMON, 'invalid_email_format', email=ex.email)
    except NotOperatingInCountryException, ex:
        error_msg = translate(lang, SOLUTION_COMMON, 'not_operating_in_country', country=ex.country)
    except BusinessException:
        logging.exception('Failed to create association, unexpected BusinessException')
        error_msg = translate(lang, SOLUTION_COMMON, 'failed_to_create_association')
    except:
        logging.exception('Failed to create association')
        error_msg = translate(lang, SOLUTION_COMMON, 'failed_to_create_association')
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
    except EmptyValueException, ex:
        val_name = translate(lang, SOLUTION_COMMON, ex.value_name)
        error_msg = translate(lang, SOLUTION_COMMON, 'empty_field_error', field_name=val_name)
    except:
        logging.exception('Could not save association service information')
        error_msg = translate(lang, SOLUTION_COMMON, 'failed_to_create_association')
    finally:
        if not success2:
            if is_new_association:
                logging.warn('Failed to save new association service information, reverting changes...')
                db.delete(db.GqlQuery("SELECT __key__ WHERE ANCESTOR IS KEY('%s')" % customer_key).fetch(None))
            return ReturnStatusTO.create(False, error_msg)
        else:
            if email_changed:
                migrate_user(users.User(customer.user_email), users.User(customer.user_email), users.User(user_email),
                             customer.service_email)
                customer.user_email = user_email
                customer.put()
            return RETURNSTATUS_TO_SUCCESS


@rest('/common/associations/delete', 'post', read_only_access=False)
@returns(ReturnStatusTO)
@arguments(service_email=unicode)
def rest_delete_association(service_email):
    customer = Customer.get_by_service_email(service_email)
    cancel_subscription(customer.id, Customer.DISABLED_REASONS[Customer.DISABLED_ASSOCIATION_BY_CITY], True)
    send_message(users.get_current_user(),
                 [{u"type": u"solutions.common.associations.deleted", u'service_email': service_email}])
    return RETURNSTATUS_TO_SUCCESS
