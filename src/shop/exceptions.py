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


# Service creation/update exceptions


class ModulesNotAllowedException(BusinessException):
    def __init__(self, disallowed_modules):
        self.disallowed_modules = disallowed_modules
        BusinessException.__init__(self, "This customer cannot have the following module(s): %s." % ", ".join(
                map(replace_underscores, disallowed_modules)))


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
