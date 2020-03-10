# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

from types import NoneType

from google.appengine.ext import db

from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from rogerthat.dal import generator
from rogerthat.dal.app import get_apps_by_id
from rogerthat.models import App
from rogerthat.rpc import users
from shop.models import Customer, CustomerSignup, ShopLoyaltySlide, ShopLoyaltySlideNewOrder, LegalEntity, ShopApp


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


@cached(1, lifetime=0, request=False, memcache=False, datastore=u"get_mobicage_legal_entity")
@returns(LegalEntity)
@arguments()
def get_mobicage_legal_entity():
    @db.non_transactional
    def get():
        return LegalEntity.all().filter('is_mobicage', True).get()
    return get()


@returns([CustomerSignup])
@arguments(city_customer=Customer, done=bool)
def get_customer_signups(city_customer, done=False):
    return list(CustomerSignup.all().ancestor(city_customer.key()).filter('done =', done))


@returns([App])
@arguments()
def get_all_signup_enabled_apps():
    signup_enabled_app_keys = ShopApp.list_signup_enabled(True).fetch(keys_only=True)
    app_ids = [app_key.id() for app_key in signup_enabled_app_keys]
    return [app for app in get_apps_by_id(app_ids) if app.main_service]
