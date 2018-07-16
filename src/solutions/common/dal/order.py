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
# @@license_version:1.2@@

from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from solutions import translate
from solutions.common import SOLUTION_COMMON
from solutions.common.models import SolutionSettings
from solutions.common.models.order import SolutionOrder, SolutionOrderSettings
from solutions.common.utils import create_service_identity_user_wo_default


@returns(SolutionOrderSettings)
@arguments(sln_settings=SolutionSettings)
def get_solution_order_settings(sln_settings):
    # type: (SolutionSettings) -> SolutionOrderSettings
    solution_order_settings_key = SolutionOrderSettings.create_key(sln_settings.service_user)
    solution_order_settings = SolutionOrderSettings.get(solution_order_settings_key)
    if not solution_order_settings:
        solution_order_settings = SolutionOrderSettings(key=solution_order_settings_key)
        solution_order_settings.text_1 = translate(sln_settings.main_language, SOLUTION_COMMON, 'order-flow-details')
        solution_order_settings.put()
    return solution_order_settings


@returns([SolutionOrder])
@arguments(service_user=users.User, service_identity=unicode)
def get_solution_orders(service_user, service_identity):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    return SolutionOrder.list(service_identity_user)
