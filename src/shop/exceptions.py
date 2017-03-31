# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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
import sys

from rogerthat.rpc.service import BusinessException


# Customer/contact exceptions


class DuplicateCustomerNameException(BusinessException):
    def __init__(self, name):
        self.name = name
        msg = 'There already exists a customer with name \"%s\". If you continue, there will be 2 customers with the' \
              ' same name.' % name
        super(DuplicateCustomerNameException, self).__init__(msg)


class CustomerNotFoundException(BusinessException):
    def __init__(self, customer_id=None, service_email=None):
        self.customer_id = customer_id
        self.service_email = service_email
        if service_email is not None:
            msg = 'Customer with service email %s not found' % service_email
        else:
            msg = 'Customer with id %d not found' % customer_id
        logging.error(msg)
        BusinessException.__init__(self, msg)


class ContactNotFoundException(BusinessException):
    def __init__(self, contact_id):
        msg = 'Contact with id %d not found' % contact_id
        logging.error(msg)
        BusinessException.__init__(self, msg)


class ContactHasOrdersException(BusinessException):
    def __init__(self, contact_id):
        msg = 'Contact with id %s has one or more orders assigned to it so it cannot be deleted.' % contact_id
        BusinessException.__init__(self, msg)


class ContactHasCreditCardException(BusinessException):
    def __init__(self, contact_id):
        msg = 'Contact with id %s has one or more credit cards assigned to it so it cannot be deleted.' % contact_id
        BusinessException.__init__(self, msg)

# Order exceptions


class NoProductsSelectedException(BusinessException):
    def __init__(self):
        BusinessException.__init__(self, 'No products selected')


class ProductNotFoundException(BusinessException):
    def __init__(self, product_name):
        self.product_name = product_name
        BusinessException.__init__(self, "Product \"%s\" does not exist." % product_name)


class InvalidProductAmountException(BusinessException):
    def __init__(self, amount, product_name):
        self.amount = amount
        self.product_name = product_name
        BusinessException.__init__(self,
                                   '%d is not a valid amount of items for product \"%s\"' % (amount, product_name))


class ProductNotAllowedException(BusinessException):
    def __init__(self, product_description):
        self.product_description = product_description
        BusinessException.__init__(self, "Product \"%s\" is not allowed for this customer." % product_description)


class NoSubscriptionFoundException(BusinessException):
    def __init__(self, customer):
        self.customer = customer
        BusinessException.__init__(self, 'No subscription found for customer %s' % customer.name)


class InvalidProductQuantityException(BusinessException):
    def __init__(self, product_description, dependency_description):
        BusinessException.__init__(self, "\"%s\" cannot be ordered without the same quantity \"%s\"." % (
            product_description, dependency_description))


class MissingProductDependencyException(BusinessException):
    def __init__(self, product_description, dependency_description):
        self.product_description = product_description
        self.dependency_description = dependency_description
        BusinessException.__init__(self,
                                   "\"%s\" cannot be ordered without \"%s\" in this or a previously signed order." % (
                                       product_description, dependency_description))


class ReplaceBusinessException(BusinessException):
    def __init__(self, existing_subscription_order_number):
        self.existing_subscription_order_number = existing_subscription_order_number
        BusinessException.__init__(self, "Customer already has a subscription: %s" % existing_subscription_order_number)


class TooManyAppsException(BusinessException):
    def __init__(self, extra_apps_count, total_extra_app_count):
        BusinessException.__init__(self, 'You cannot order %s extra apps because there are only %s available'
                                   % (extra_apps_count, total_extra_app_count))


class NoSubscriptionException(BusinessException):
    def __init__(self, customer):
        self.customer = customer
        BusinessException.__init__(self, 'Customer %s has no subscription yet' % customer.name)


class OrderAlreadyCanceledException(BusinessException):
    def __init__(self, order):
        self.order = order
        BusinessException.__init__(self, 'Order %s has already been canceled' % order.order_number)


# Service creation/update exceptions


class NoOrderException(BusinessException):
    def __init__(self):
        BusinessException.__init__(self,
                                   "This customer does not have an order yet. First create an order for this customer.")


class ModulesNotAllowedException(BusinessException):
    def __init__(self, disallowed_modules):
        self.disallowed_modules = disallowed_modules
        BusinessException.__init__(self, "This customer cannot have the following module(s): %s." % ", ".join(
                map(replace_underscores, disallowed_modules)))


class InvalidAppCountException(BusinessException):
    def __init__(self, max_app_count):
        self.max_app_count = max_app_count
        extraS = 's' if self.max_app_count != 1 else ''
        BusinessException.__init__(self, 'This customer should have exactly %d active application%s.' % (
            max_app_count, extraS))


class InvalidServiceEmailException(BusinessException):
    def __init__(self, email):
        self.email = email
        BusinessException.__init__(self, "This customer already had a service, but with e-mail address '%s'" % email)


class InvalidEmailFormatException(BusinessException):
    def __init__(self, email):
        self.email = email
        BusinessException.__init__(self, '\"%s\" is not a valid email address.' % email)


# Misc. exceptions


class EmptyValueException(BusinessException):
    def __init__(self, value_name):
        # value_name has to be a translate key in common translation
        self.value_name = value_name
        BusinessException.__init__(self, "The value \"%s\" is not filled in." % replace_underscores(value_name))


class ServiceNameTooBigException(BusinessException):
    def __init__(self):
        BusinessException.__init__(self, "Invalid service name (length > 50 characters)")


class InvalidLanguageException(BusinessException):
    def __init__(self, lang):
        self.lang = lang
        BusinessException.__init__(self, "The language \"%s\" is not supported." % lang)


class NotOperatingInCountryException(BusinessException):
    def __init__(self, country):
        self.country = country
        msg = 'Sorry, we currently do not operate in %s yet.' % country
        logging.error(msg)
        BusinessException.__init__(self, msg)


class NoPermissionException(BusinessException):
    def __init__(self, action=None):
        self.action = action
        BusinessException.__init__(self, 'You don\'t have permission to execute this action (%s)' % replace_underscores(
            self.action or sys._getframe(1).f_code.co_name))


class AppNotFoundException(BusinessException):
    def __init__(self, app_id):
        self.app_id = app_id
        BusinessException.__init__(self, 'App with id %s does not exist' % app_id)


class NoCreditCardException(BusinessException):
    def __init__(self, customer):
        self.customer = customer
        BusinessException.__init__(self, 'customer %s has no credit hard linked' % customer.name)


def replace_underscores(value):
    return value.replace('_', ' ').capitalize()


# Regiomanager and RegiomanagerTeam exceptions

class NoSupportManagerException(BusinessException):
    def __init__(self, team):
        self.team = team
        BusinessException.__init__(self, 'Regiomanager team %s has no support manager' % team.name)
