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

from google.appengine.ext import db

from mcfw.rpc import serialize_complex_value

from rogerthat.models import ServiceIdentity, ServiceProfile
from rogerthat.utils import channel
from rogerthat.utils.transactions import run_in_xg_transaction

from shop.bizz import put_customer_with_service, put_service
from shop.models import Product, RegioManagerTeam

from solutions import SOLUTION_COMMON, translate as common_translate
from solutions.common.bizz import SolutionModule, DEFAULT_BROADCAST_TYPES, ASSOCIATION_BROADCAST_TYPES, send_email
from solutions.common.dal import get_solution_settings, get_solution_settings_or_identity_settings
from solutions.common.to import SolutionInboxMessageTO


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


def filter_modules(city_customer, modules, broadcast_types):
    """Given a modules list, it will return the mandatory and allowed modules and discard others.

    Args:
        city_customer (Customer): city customer
        modules (list of unicode)
        broadcast_type (list of unicode)
    """
    mods = [m for m in SolutionModule.MANDATORY_MODULES]
    mods.extend([m for m in modules if m in get_allowed_modules(city_customer)])
    modules = list(set(mods))

    if SolutionModule.BROADCAST in modules and not broadcast_types:
        modules.remove(SolutionModule.BROADCAST)

    return modules


def create_customer_with_service(city_customer, customer, service, name, address1, address2, zip_code,
                                 city, language,  organization_type, vat, website=None, facebook_page=None):
    """Given a customer and a service, will create the customer, contact and order."""

    customer_id = customer.id if customer else None
    if not customer and organization_type not in city_customer.editable_organization_types:
        organization_type = city_customer.editable_organization_types[0]

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

    return put_customer_with_service(service, name, address1, address2, zip_code, city, city_customer.country, language,
                                     organization_type, vat, city_customer.team_id, product_code, customer_id,
                                     website, facebook_page)


def put_customer_service(customer, service, search_enabled, skip_module_check, skip_email_check, rollback=False):
    """Put the service, if rolllback is set, it will remove the customer in case of failure."""

    customer_key = customer.key()

    def trans():
        put_service(customer, service, skip_module_check=skip_module_check, search_enabled=search_enabled,
                    skip_email_check=skip_email_check)

    try:
        run_in_xg_transaction(trans)
    except Exception as e:
        if rollback:
            db.delete(db.GqlQuery("SELECT __key__ WHERE ANCESTOR IS KEY('%s')" % customer_key).fetch(None))
        raise e


def _send_approved_signup_email(city_customer, signup, lang):
    def trans(term, *args, **kwargs):
        return common_translate(lang, SOLUTION_COMMON, unicode(term))

    subject = u'{} - {}'.format(trans('our-city-app'), trans('signup_application'))
    message = trans('signup_approval_email_message', name=signup.customer_name, city_name=city_customer.name)

    send_email(subject, city_customer.user_email, [signup.customer_email], [], None, message)


def _send_denied_signup_email(city_customer, signup, lang, reason):
    subject = common_translate(city_customer.language, SOLUTION_COMMON,
                               u'can_not_fulfil_signup_application', city=city_customer.name)
    send_email(subject, city_customer.user_email, [signup.customer_email], [], None, reason)


def set_customer_signup_done(city_customer, signup, approved, reason=None):
    """Set the customer signup to done and move the inbox message to trash"""

    def trans():
        to_put = [signup]
        inbox_message = None
        signup.done = True
        if signup.inbox_message_key:
            inbox_message = db.get(signup.inbox_message_key)
            if inbox_message:
                inbox_message.trashed = True
                to_put.append(inbox_message)

        db.put(to_put)
        return inbox_message

    message = run_in_xg_transaction(trans)
    if message:
        service_user = signup.parent().service_user
        sln_settings = get_solution_settings(service_user)

        if approved:
            _send_approved_signup_email(city_customer, signup, sln_settings.main_language)
        else:
            _send_denied_signup_email(city_customer, signup, sln_settings.main_language, reason)

        service_identity = ServiceIdentity.DEFAULT
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        message_to = SolutionInboxMessageTO.fromModel(message, sln_settings, sln_i_settings, True)
        channel.send_message(service_user, u'solutions.common.messaging.update',
                             service_identity=service_identity,
                             message=serialize_complex_value(message_to, SolutionInboxMessageTO, False))

