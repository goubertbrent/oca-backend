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

from datetime import datetime

from rogerthat.bizz.job import run_job
from rogerthat.bizz.service import re_index_map_only
from rogerthat.utils import try_or_defer
from rogerthat.utils.service import create_service_identity_user
from shop.models import Customer
from solutions.common.integrations.cirklo.cirklo import check_merchant_whitelisted
from solutions.common.integrations.cirklo.models import VoucherSettings, CirkloMerchant, VoucherProviderId


def job(app_id, city_id):
    run_job(_qry, [app_id], _worker, [city_id])


def _qry(app_id):
    return VoucherSettings.query().filter(VoucherSettings.app_id == app_id)


def _worker(vouchers_key, city_id):
    voucher_settings = vouchers_key.get()
    provider = voucher_settings.get_provider(VoucherProviderId.CIRKLO)
    if not provider:
        return

    service_user_email = voucher_settings.service_user.email()
    cirklo_merchant_key = CirkloMerchant.create_key(service_user_email)
    current_cirklo_merchant = cirklo_merchant_key.get()
    if current_cirklo_merchant:
        return

    customer = Customer.get_by_service_email(service_user_email)
    if not customer:
        return

    cirklo_merchant = CirkloMerchant(key=cirklo_merchant_key)
    cirklo_merchant.creation_date = datetime.utcfromtimestamp(customer.creation_time)
    cirklo_merchant.service_user_email = service_user_email
    cirklo_merchant.customer_id = customer.id
    cirklo_merchant.city_id = city_id
    cirklo_merchant.data = None
    cirklo_merchant.whitelisted = check_merchant_whitelisted(city_id, customer.user_email)
    cirklo_merchant.denied = False
    cirklo_merchant.put()

    service_identity_user = create_service_identity_user(customer.service_user)
    try_or_defer(re_index_map_only, service_identity_user)
