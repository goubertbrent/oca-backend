# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

from google.appengine.ext import db

from rogerthat.bizz.profile import set_service_disabled as rogerthat_set_service_disabled, \
    set_service_enabled as rogerthat_re_enable_service
from rogerthat.dal.service import get_service_identity
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.utils import now
from mcfw.rpc import arguments, returns
from rogerthat.utils.service import create_service_identity_user
from shop.exceptions import NoSubscriptionException
from shop.models import Customer
from solutions.common.dal import get_solution_settings


@returns()
@arguments(customer_or_id=(int, long, Customer), disabled_reason_int=(int, long))
def set_service_disabled(customer_or_id, disabled_reason_int):
    """
    Disables the customer his service, disconnects all users and sets the service invisible.

    Args:
        customer_or_id (int, long, Customer): customer or id
        disabled_reason_int (int, long): reason why the service has been disabled

    Raises:
        NoSubscriptionException
        BusinessException
    """
    if isinstance(customer_or_id, Customer):
        customer = customer_or_id
    else:
        customer = Customer.get_by_id(customer_or_id)

    if not customer.service_email:
        raise NoSubscriptionException(customer)
    if disabled_reason_int not in Customer.DISABLED_REASONS:
        raise BusinessException('Invalid disable service reason')

    service_user = users.User(customer.service_email)
    sln_settings = get_solution_settings(service_user)
    customer.default_app_id = None
    customer.app_ids = []
    customer.service_disabled_at = now()
    customer.disabled_reason_int = disabled_reason_int
    customer.subscription_cancel_pending_date = 0
    sln_settings.search_enabled = False
    sln_settings.service_disabled = True
    db.put([customer, sln_settings])

    rogerthat_set_service_disabled(service_user)


@returns()
@arguments(customer_id=int)
def set_service_enabled(customer_id):
    customer = Customer.get_by_id(customer_id)
    if not customer.service_email:
        raise NoSubscriptionException(customer)

    service_user = users.User(customer.service_email)
    service_identity_user = create_service_identity_user(service_user)
    si = get_service_identity(service_identity_user)
    sln_settings = get_solution_settings(service_user)
    sln_settings.service_disabled = False
    customer.service_disabled_at = 0
    customer.disabled_reason = u''
    customer.disabled_reason_int = 0
    customer.subscription_cancel_pending_date = 0
    # restore app ids
    customer.app_ids = si.sorted_app_ids
    customer.default_app_id = si.app_id
    db.put([customer, sln_settings])

    rogerthat_re_enable_service(service_user)
