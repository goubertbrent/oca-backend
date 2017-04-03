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
# @@license_version:1.3@@

from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from shop.models import Customer, Order, OrderItem
from rogerthat.rpc import users
from solutions.common.dal import get_solution_settings


def job():
    deferred.defer(_add_properties)


def _add_properties():
    customers = Customer.all()
    to_put = list()
    for customer in customers:
        if customer.subscription_order_number:
            order_key = Order.create_key(customer.id, customer.subscription_order_number)
            order = Order.get(order_key)
            customer.creation_time = order.date
            customer.subscription_type = 0 if OrderItem.all(keys_only=True).ancestor(order_key).filter('product_code',
                                                                                                       'MSSU').get() else 1
        else:
            customer.creation_time = 0  # at this point it's not known when the customer was created
        if customer.service_email:
            service_user = users.User(email=customer.service_email)
            sln_settings = get_solution_settings(service_user)
            customer.has_loyalty = True if u'loyalty' in sln_settings.modules else False
        else:
            customer.has_loyalty = False
        to_put.append(customer)
    db.put(to_put)
