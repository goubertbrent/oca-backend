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

import logging

from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from solutions.common.dal import get_solution_settings
from solutions.common.dal.hints import get_all_solution_hints, get_solution_hints, get_solution_hint_settings
from solutions.common.to.hints import SolutionHintTO


@rest("/common/hints/load_next", "get", read_only_access=True)
@returns(SolutionHintTO)
@arguments()
def hints_load():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    solution_hint_settings = get_solution_hint_settings(service_user)

    hint_ids = get_solution_hints().hint_ids
    for hint_id in solution_hint_settings.do_not_show_again:
        try:
            hint_ids.remove(hint_id)
        except:
            logging.debug("Hint with id '%s' does not exist anymore", hint_id)

    for h in get_all_solution_hints(hint_ids):
        if (not h.modules or any(module in sln_settings.modules for module in h.modules)):
            if sln_settings.main_language == h.language:
                return SolutionHintTO.fromModel(h)
    return None


@rest("/common/hints/mark_read", "post")
@returns(ReturnStatusTO)
@arguments(hint_id=(int, long))
def hints_mark_as_read(hint_id):
    service_user = users.get_current_user()
    try:
        solution_hint_settings = get_solution_hint_settings(service_user)
        if hint_id not in solution_hint_settings.do_not_show_again:
            solution_hint_settings.do_not_show_again.append(hint_id)
            solution_hint_settings.put()

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)
