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

from rogerthat.dal import  generator, parent_key_unsafe
from rogerthat.rpc import users
from mcfw.rpc import returns, arguments
from solutions.common.models.repair import SolutionRepairSettings, SolutionRepairOrder
from solutions.common.utils import create_service_identity_user_wo_default


@returns(SolutionRepairSettings)
@arguments(service_user=users.User)
def get_solution_repair_settings(service_user):
    return SolutionRepairSettings.get(SolutionRepairSettings.create_key(service_user))

@returns([SolutionRepairOrder])
@arguments(service_user=users.User, service_identity=unicode, solution=unicode, cursor=unicode)
def get_solution_repair_orders(service_user, service_identity, solution, cursor=None):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    qry = SolutionRepairOrder.gql("WHERE ANCESTOR IS :ancestor AND deleted=False ORDER BY timestamp DESC")
    qry.with_cursor(cursor)
    qry.bind(ancestor=parent_key_unsafe(service_identity_user, solution))
    return generator(qry.run())
