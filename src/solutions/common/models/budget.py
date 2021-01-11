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

from __future__ import unicode_literals

from google.appengine.ext import ndb

from rogerthat.dal import parent_ndb_key
from rogerthat.models.common import NdbModel
from solutions import SOLUTION_COMMON


class BudgetOrderStatus(object):
    ORDERED = 0
    PAID = 1


class BudgetOrder(NdbModel):
    date = ndb.DateTimeProperty(auto_now_add=True)
    service_email = ndb.StringProperty()
    status = ndb.IntegerProperty(default=BudgetOrderStatus.ORDERED)

    @property
    def paid(self):
        return self.status == BudgetOrderStatus.PAID

    @classmethod
    def list_by_service(cls, service_email):
        return cls.query().filter(cls.service_email == service_email)


class Budget(NdbModel):
    DEFAULT_NAME = 'main'

    balance = ndb.IntegerProperty(default=0)

    @classmethod
    def create_key(cls, user, name=None):
        return ndb.Key(cls, name or cls.DEFAULT_NAME, parent=parent_ndb_key(user, SOLUTION_COMMON))


class BudgetTransaction(NdbModel):
    TYPE_NEWS = 'news'

    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    amount = ndb.IntegerProperty()
    service_identity = ndb.StringProperty()
    context_type = ndb.StringProperty()
    context_key = ndb.KeyProperty()
    memo = ndb.StringProperty()

    @classmethod
    def list_by_user(cls, user, budget_name=None):
        return cls.query(ancestor=Budget.create_key(user, budget_name)).order(cls.timestamp)
