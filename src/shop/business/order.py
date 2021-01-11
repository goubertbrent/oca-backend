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
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.business.service import set_service_disabled
from shop.exceptions import EmptyValueException
from shop.models import Customer


@returns()
@arguments(customer_id=(int, long), cancel_reason=unicode)
def cancel_subscription(customer_id, cancel_reason):
    """
    Disable the service and disconnect all users.

    Args:
        customer_id (int, long): Customer id
        cancel_reason (unicode): Reason why the subscription has been canceled.

    Returns: None

    Raises:
        EmptyValueException
        CustomerNotFoundException
    """
    if not cancel_reason:
        raise EmptyValueException('cancel_reason')

    customer = Customer.get_by_id(customer_id)

    def trans():
        customer.disabled_reason = cancel_reason
        set_service_disabled(customer, Customer.DISABLED_OTHER)

    run_in_xg_transaction(trans)
