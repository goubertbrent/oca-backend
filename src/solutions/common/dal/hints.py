# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

from rogerthat.rpc import users
from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from solutions.common.models.hints import SolutionHints, SolutionHint, SolutionHintSettings


@returns(SolutionHintSettings)
@arguments(service_user=users.User)
def get_solution_hint_settings(service_user):
    shs_key = SolutionHintSettings.create_key(service_user)
    shs = SolutionHintSettings.get(shs_key)
    if not shs:
        shs = SolutionHintSettings(key=shs_key)
    return shs

@returns([SolutionHint])
@arguments(hint_ids=[(int, long)])
def get_all_solution_hints(hint_ids):
    if hint_ids:
        return SolutionHint.get_by_id(hint_ids)
    else:
        return []

@cached(1)
@returns(SolutionHints)
@arguments()
def get_solution_hints():
    sln_hints = SolutionHints.get_by_key_name("SolutionHints")
    if not sln_hints:
        sln_hints = SolutionHints(key_name="SolutionHints")
    return sln_hints
