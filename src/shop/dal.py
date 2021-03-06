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

from mcfw.rpc import returns, arguments
from rogerthat.dal import generator
from rogerthat.rpc import users
from shop.models import Customer, CustomerSignup, ShopLoyaltySlide, ShopLoyaltySlideNewOrder


@returns(Customer)
@arguments(service_user=users.User)
def get_customer(service_user):
    # type: (users.User) -> Customer
    return Customer.get_by_service_email(service_user.email())


@returns([ShopLoyaltySlide])
@arguments(app_id=unicode)
def get_shop_loyalty_slides(app_id=None):
    result = []
    if app_id:
        qry = ShopLoyaltySlide.gql("WHERE deleted=False AND has_apps=False ORDER BY timestamp DESC")
        result.extend(generator(qry.run()))
        qry = ShopLoyaltySlide.gql("WHERE deleted=False AND apps = :app_id ORDER BY timestamp DESC")
        qry.bind(app_id=app_id)
        result.extend(generator(qry.run()))
    else:
        qry = ShopLoyaltySlide.gql("WHERE deleted=False ORDER BY timestamp DESC")
        result.extend(generator(qry.run()))
    return result


@returns([ShopLoyaltySlideNewOrder])
@arguments()
def get_shop_loyalty_slides_new_order():
    return generator(ShopLoyaltySlideNewOrder.all())


@returns([CustomerSignup])
@arguments(city_customer=Customer, done=bool)
def get_customer_signups(city_customer, done=False):
    return list(CustomerSignup.all().ancestor(city_customer.key()).filter('done =', done))
