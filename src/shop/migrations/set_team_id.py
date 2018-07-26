# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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

from rogerthat.bizz.job import run_job
from google.appengine.ext import db
from shop.models import Customer, Order, Charge, RegioManager


def job(default_team_id):
    run_job(_all_customers, [],
            _add_team_id, [default_team_id])


def _all_customers():
    return Customer.all()


def _add_team_id(customer, default_team_id):
    team_ids = {}
    to_put = []

    def _add_team_id_for_manager(manager_email):
        regio_manager = RegioManager.get(RegioManager.create_key(manager_email))
        if regio_manager and regio_manager.team_id:
            team_ids[manager_email] = regio_manager.team_id

    to_put.append(customer)
    if customer.manager:
        _add_team_id_for_manager(customer.manager.email())
        if customer.manager.email() in team_ids:
            customer.team_id = team_ids[customer.manager.email()]
        else:
            customer.team_id = default_team_id

        for order in Order.all().ancestor(customer):
            to_put.append(order)
            if order.manager:
                if order.manager.email() not in team_ids:
                    _add_team_id_for_manager(order.manager.email())

                if order.manager.email() in team_ids:
                    order.team_id = team_ids[order.manager.email()]
                else:
                    order.team_id = default_team_id
            else:
                order.team_id = default_team_id

        for charge in Charge.all().ancestor(customer):
            to_put.append(charge)
            if charge.manager:
                if charge.manager.email() not in team_ids:
                    _add_team_id_for_manager(charge.manager.email())

                if charge.manager.email() in team_ids:
                    charge.team_id = team_ids[charge.manager.email()]
                else:
                    charge.team_id = default_team_id
            else:
                charge.team_id = default_team_id

    else:
        customer.team_id = default_team_id
        for order in Order.all().ancestor(customer):
            to_put.append(order)
            order.team_id = default_team_id
        for charge in Charge.all().ancestor(customer):
            to_put.append(charge)
            charge.team_id = default_team_id

    if to_put:
        db.put(to_put)
