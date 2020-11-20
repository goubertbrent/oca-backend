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
from typing import List

from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from solutions.common.models.hints import SolutionHints, SolutionHint, \
    SolutionHintSettings


@returns(SolutionHintSettings)
@arguments(service_user=users.User)
def get_solution_hint_settings(service_user):
    # type: (users.User) -> SolutionHintSettings
    hint_settings_key = SolutionHintSettings.create_key(service_user)
    hint_settings = hint_settings_key.get()
    if not hint_settings:
        hint_settings = SolutionHintSettings(key=hint_settings_key)
    return hint_settings


def get_all_solution_hints(hint_ids):
    # type: (List[int]) -> List[SolutionHint]
    return ndb.get_multi(SolutionHint.create_key(hint_id) for hint_id in hint_ids)


def get_solution_hints():
    # type: () -> SolutionHints
    key = SolutionHints.create_key()
    sln_hints = key.get()
    if not sln_hints:
        sln_hints = SolutionHints(key=key)
    return sln_hints
