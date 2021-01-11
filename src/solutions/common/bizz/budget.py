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

from google.appengine.ext import ndb

from solutions.common.models.budget import Budget, BudgetTransaction


BUDGET_RATE = 2.0  # 10k views / 5000 cent


@ndb.transactional(xg=True)
def update_budget(service_user, amount, service_identity=None, context_type=None, context_key=None, memo=None):
    budget_key = Budget.create_key(service_user)
    budget = budget_key.get() or Budget(key=budget_key)

    budget_transaction = BudgetTransaction(parent=budget_key,
                                           context_type=context_type,
                                           context_key=context_key,
                                           amount=amount,
                                           memo=memo,
                                           service_identity=service_identity)
    prev_transactions = BudgetTransaction.query(ancestor=budget_key)
    new_balance = sum([transaction.amount for transaction in prev_transactions]) + amount
    budget.balance = new_balance

    ndb.put_multi([budget, budget_transaction])
    return budget, budget_transaction
