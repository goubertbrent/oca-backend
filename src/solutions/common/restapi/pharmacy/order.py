# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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

from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from solutions.common.bizz.pharmacy.order import delete_pharmacy_order, send_message_for_pharmacy_order
from solutions.common.dal.pharmacy.order import get_solution_pharmacy_orders
from solutions.common.to.pharmacy.order import SolutionPharmacyOrderTO


@rest("/common/pharmacy_order/delete", "post")
@returns(ReturnStatusTO)
@arguments(order_key=unicode, message=unicode)
def order_delete(order_key, message):
    service_user = users.get_current_user()
    try:
        delete_pharmacy_order(service_user, order_key, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)

@rest("/common/pharmacy_orders/load", "get", read_only_access=True)
@returns([SolutionPharmacyOrderTO])
@arguments()
def orders_load():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    return map(SolutionPharmacyOrderTO.fromModel, get_solution_pharmacy_orders(service_user, service_identity))

@rest("/common/pharmacy_order/sendmessage", "post")
@returns(ReturnStatusTO)
@arguments(order_key=unicode, order_status=int, message=unicode)
def order_send_message(order_key, order_status, message):
    service_user = users.get_current_user()
    try:
        send_message_for_pharmacy_order(service_user, order_key, order_status, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)
