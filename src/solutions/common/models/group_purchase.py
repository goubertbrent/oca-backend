# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

from rogerthat.dal import parent_key, parent_key_unsafe
from rogerthat.rpc import users
from rogerthat.utils.service import get_identity_from_service_identity_user, \
    get_service_user_from_service_identity_user
from google.appengine.ext import db
from solutions.common.models.properties import SolutionUserProperty
from solutions.common.utils import create_service_identity_user_wo_default


class SolutionGroupPurchaseSettings(db.Model):
    visible = db.BooleanProperty(indexed=False, default=True)
    branding_hash = db.StringProperty(indexed=False)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    def create_key(service_user, solution):
        return db.Key.from_path(SolutionGroupPurchaseSettings.kind(), service_user.email(),
                                parent=parent_key(service_user, solution))

class SolutionGroupPurchase(db.Model):
    title = db.StringProperty(indexed=False)
    description = db.TextProperty(indexed=False)
    picture = db.BlobProperty(indexed=False)
    picture_version = db.IntegerProperty(indexed=False, default=0)
    units = db.IntegerProperty(indexed=False)
    unit_description = db.TextProperty(indexed=False)
    unit_price = db.IntegerProperty(indexed=False)  # in euro cents
    min_units_pp = db.IntegerProperty(indexed=False)
    max_units_pp = db.IntegerProperty(indexed=False)
    time_from = db.IntegerProperty()  # epoch
    time_until = db.IntegerProperty()  # epoch
    deleted = db.BooleanProperty(default=False)

    @property
    def unit_price_in_euro(self):
        return u'{:20,.2f}'.format(self.unit_price / 100.0).strip()

    @property
    def id(self):
        return self.key().id()

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @property
    def subscriptions(self):
        return SolutionGroupPurchaseSubscription.all().ancestor(self)

    def subscriptions_for_user(self, app_user):
        return SolutionGroupPurchaseSubscription.all().ancestor(self).filter('app_user =', app_user)

    @property
    def units_available(self):
        available_units = self.units
        for e in self.subscriptions:
            available_units -= e.units
        return available_units

    @staticmethod
    def list(service_user, service_identity, solution):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return SolutionGroupPurchase.all().ancestor(parent_key_unsafe(service_identity_user, solution)).filter('deleted', False)


class SolutionGroupPurchaseSubscription(db.Model):
    sender = SolutionUserProperty(indexed=False)  # app
    name = db.StringProperty(indexed=False)  # cms
    units = db.IntegerProperty(indexed=False)
    timestamp = db.IntegerProperty(indexed=False)
    app_user = db.UserProperty(indexed=True)

    @property
    def id(self):
        return self.key().id()

    @property
    def solution_group_purchase_key(self):
        return self.parent_key()

    @property
    def solution_group_purchase(self):
        return SolutionGroupPurchase.get(self.solution_group_purchase_key)
