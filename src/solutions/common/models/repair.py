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

from rogerthat.dal import parent_key
from rogerthat.rpc import users
from rogerthat.utils.service import get_identity_from_service_identity_user, \
    get_service_user_from_service_identity_user
from google.appengine.ext import db
from solutions.common import SOLUTION_COMMON
from solutions.common.models.properties import SolutionUserProperty


class SolutionRepairSettings(db.Model):
    text_1 = db.TextProperty()

    @classmethod
    def create_key(cls, service_user):
        return db.Key.from_path(cls.kind(), service_user.email(),
                                parent=parent_key(service_user, SOLUTION_COMMON))

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

class SolutionRepairOrder(db.Model):
    STATUS_RECEIVED = 1
    STATUS_COMPLETED = 2

    REPAIR_ORDER_STATUSES = (STATUS_RECEIVED, STATUS_COMPLETED)

    timestamp = db.IntegerProperty(indexed=True)
    user = db.UserProperty(indexed=True)
    deleted = db.BooleanProperty(indexed=True, default=False)
    status = db.IntegerProperty(indexed=False)
    description = db.TextProperty(indexed=False)
    sender = SolutionUserProperty()
    picture_url = db.TextProperty(indexed=False)

    solution_inbox_message_key = db.StringProperty(indexed=False)

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
    def solution_repair_order_key(self):
        return str(self.key())
