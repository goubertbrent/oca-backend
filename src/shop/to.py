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

from mcfw.properties import unicode_property, long_property, bool_property, unicode_list_property, typed_property, \
    float_property, long_list_property
from mcfw.rpc import serialize_complex_value
from rogerthat.to import ReturnStatusTO, TO


class CompanyTO(object):
    name = unicode_property('1')
    address1 = unicode_property('2')
    address2 = unicode_property('3')
    zip_code = unicode_property('4')
    city = unicode_property('5')
    country = unicode_property('6')
    vat = unicode_property('7')
    organization_type = long_property('8')
    user_email = unicode_property('9')
    telephone = unicode_property('10')
    website = unicode_property('11')
    facebook_page = unicode_property('12')


class CustomerTO(CompanyTO):
    id = long_property('51')
    service_email = unicode_property('52')
    auto_login_url = unicode_property('54')
    migration_job = unicode_property('56')
    language = unicode_property('61')
    creation_time = long_property('64')
    service_disabled_at = long_property('68')
    service_disabled_reason = unicode_property('69')
    service_disabled_reason_int = long_property('70')
    community_id = long_property('community_id')

    @staticmethod
    def fromCustomerModel(customer):
        c = CustomerTO()
        c.name = customer.name
        c.address1 = customer.address1
        c.address2 = customer.address2
        c.zip_code = customer.zip_code
        c.city = customer.city
        c.country = customer.country
        c.vat = customer.vat
        c.organization_type = customer.organization_type
        c.id = customer.id
        c.service_email = customer.service_email
        c.user_email = customer.user_email
        c.auto_login_url = customer.auto_login_url if customer.service_email else None
        c.migration_job = customer.migration_job
        c.language = customer.language
        c.creation_time = customer.creation_time
        c.service_disabled_at = customer.service_disabled_at
        c.service_disabled_reason = customer.disabled_reason or customer.disabled_reason_str
        c.service_disabled_reason_int = customer.disabled_reason_int
        c.website = customer.website
        c.facebook_page = customer.facebook_page
        c.community_id = customer.community_id
        return c


class EmailConsentTO(TO):
    newsletter = bool_property('newsletter')
    email_marketing = bool_property('email_marketing')


class CustomerReturnStatusTO(ReturnStatusTO):
    customer = typed_property('51', CustomerTO)
    warning = unicode_property('52')

    @classmethod
    def create(cls, success=True, errormsg=None, customer=None, warning=None):
        r = super(CustomerReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.customer = customer
        r.warning = warning
        return r


class ContactTO(TO):
    id = long_property('0')
    first_name = unicode_property('1')
    last_name = unicode_property('2')
    email = unicode_property('3')
    phone_number = unicode_property('4')

    @staticmethod
    def fromContactModel(contact):
        c = ContactTO()
        c.id = contact.id
        c.first_name = contact.first_name
        c.last_name = contact.last_name
        c.email = contact.email
        c.phone_number = contact.phone_number
        return c


class SerializableTO(object):
    def __unicode__(self):
        return unicode(serialize_complex_value(self, self.__class__, False))


class CustomerServiceTO(TO):
    email = unicode_property('2', default=None)
    phone_number = unicode_property('4', default=None)
    language = unicode_property('5')
    modules = unicode_list_property('7')
    organization_type = long_property('10')
    managed_organization_types = long_list_property('13')
    community_id = long_property('community_id')


class ModulesReturnStatusTO(ReturnStatusTO):
    modules = unicode_list_property('51')

    @classmethod
    def create(cls, success=True, errormsg=None, modules=None):
        r = super(ModulesReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.modules = modules or list()
        return r


class JobReturnStatusTO(ReturnStatusTO):
    job_key = unicode_property('51')

    @classmethod
    def create(cls, success=True, errormsg=None, job_key=None):
        r = super(JobReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.job_key = job_key
        return r


class JobStatusTO(object):
    progress = long_property('1')
    phase = long_property('2')

    @classmethod
    def from_model(cls, model):
        to = cls()
        to.progress = int(model.estimate_progress())
        to.phase = model.phase
        return to


class PointTO(object):
    lat = float_property('1')
    lon = float_property('2')

    @classmethod
    def create(cls, lat, lon):
        to = cls()
        to.lat = lat
        to.lon = lon
        return to


class BoolReturnStatusTO(ReturnStatusTO):
    bool = bool_property('5')

    @classmethod
    def create(cls, success=True, errormsg=None, bool_value=False):
        r = super(BoolReturnStatusTO, cls).create(success, errormsg)
        r.bool = bool_value
        return r


class SimpleAppTO(object):
    id = unicode_property('0')
    name = unicode_property('1')

    @classmethod
    def from_model(cls, model):
        app = cls()
        app.id = model.app_id
        app.name = model.name
        return app


class CustomerLocationTO(object):
    name = unicode_property('1')
    description = unicode_property('2')
    has_terminal = bool_property('3')
    lat = float_property('4')
    lon = float_property('5')
    address = unicode_property('6')
    type = long_property('7')

    def __init__(self, name=None, description=None, has_terminal=False, lat=None, lon=None, address=None, type_=None):
        self.name = name
        self.description = description
        self.has_terminal = has_terminal
        self.lat = lat
        self.lon = lon
        self.address = address
        self.type = type_


class ImportCustomersReturnStatusTO(ReturnStatusTO):
    customer_count = long_property('101')

    @classmethod
    def create(cls, success=True, errormsg=None, customer_count=0):
        status = super(ImportCustomersReturnStatusTO, cls).create(success, errormsg)
        status.customer_count = customer_count
        return status
