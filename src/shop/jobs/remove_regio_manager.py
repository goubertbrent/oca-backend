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

import logging

from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from mcfw.rpc import arguments, returns
from rogerthat.dal import put_in_chunks
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.utils import bizz_check
from rogerthat.utils.transactions import run_in_transaction
from shop.constants import STORE_MANAGER
from shop.models import RegioManager, Charge, Customer, Order, RegioManagerStatistic


@returns()
@arguments(manager_email=unicode)
def remove_regio_manager(manager_email):
    logging.info('Removing regional manager %s', manager_email)
    bizz_check(manager_email != STORE_MANAGER, 'Deleting the <Customer shop> regional manager is not allowed.')

    def trans():
        manager_key = RegioManager.create_key(manager_email)
        manager = RegioManager.get(manager_key)
        if not manager.team_id:
            raise BusinessException('Cannot delete regional manager that has no team.')
        team = manager.team
        if not team.support_manager:
            raise BusinessException('Cannot delete regional manager: Team \'%s\' has no support manager' % team.name)
        if team.support_manager == manager_email:
            raise BusinessException('You cannot delete the support manager of a team.'
                                    ' Assign this role to a different regional manager first.')
        team.regio_managers.remove(manager_email)
        db.delete([manager_key, RegioManagerStatistic.create_key(manager_email)])
        team.put()
        return team

    team = run_in_transaction(trans, xg=True)
    deferred.defer(_change_charges_manager, manager_email, team.support_manager)
    deferred.defer(_change_orders_manager, manager_email, team.support_manager)
    deferred.defer(_change_customers_manager, manager_email)


def _change_charges_manager(manager_email, replacement_manager_email):
    logging.info('Setting regional manager on charges from %s to %s', manager_email, replacement_manager_email)
    to_put = []
    replacement_user = users.User(replacement_manager_email)
    charges = Charge.all().filter('manager', users.User(manager_email)).fetch(None)
    for charge in charges:
        charge.manager = replacement_user
        to_put.append(charge)
    put_in_chunks(to_put)


def _change_orders_manager(manager_email, replacement_manager_email):
    logging.info('Setting regional manager on orders from %s to %s', manager_email, replacement_manager_email)
    to_put = []
    replacement_user = users.User(replacement_manager_email)
    orders = Order.all().filter('manager', users.User(manager_email)).fetch(None)
    for order in orders:
        order.manager = replacement_user
        to_put.append(order)
    put_in_chunks(to_put)


def _change_customers_manager(manager_email):
    logging.info('Unsetting regional manager on customers with assigned manager \'%s\'', manager_email)
    to_put = []
    manager_user = users.User(manager_email)
    for customer in Customer.all():
        if customer.manager == manager_user:
            customer.manager = None
            to_put.append(customer)
    put_in_chunks(to_put)
