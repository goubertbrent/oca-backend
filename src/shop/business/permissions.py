# -*- coding: utf-8 -*-
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.4@@
import logging

from google.appengine.api import users as gusers
from google.appengine.ext import db

from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from shop.models import RegioManager
from solution_server_settings import get_solution_server_settings
from solutions.common.models.qanda import Question


@returns(bool)
@arguments(user=users.User)
def is_admin(user):
    solutions_server_settings = get_solution_server_settings()
    return user in [gusers.User(email) for email in solutions_server_settings.shop_bizz_admin_emails]


@returns(bool)
@arguments(user=users.User)
def is_admin_or_other_legal_entity(user):
    if not is_admin(user):
        manager = RegioManager.get(RegioManager.create_key(user.email()))
        if not manager or manager.team.legal_entity.is_mobicage:
            return False
    return True


@returns(bool)
@arguments(user=users.User)
def is_payment_admin(user):
    solutions_server_settings = get_solution_server_settings()
    return user in [gusers.User(email) for email in solutions_server_settings.shop_payment_admin_emails]


@returns(bool)
@arguments(user=users.User)
def is_team_admin(user):
    manager = RegioManager.get(RegioManager.create_key(user.email()))
    return manager is not None and manager.admin


@returns(bool)
@arguments(user=users.User, team_id=(int, long))
def user_has_permissions_to_team(user, team_id):
    @db.non_transactional
    def _get_regio_manager(email):
        return RegioManager.get(RegioManager.create_key(email))

    if is_admin(user):
        return True
    regio_manager = _get_regio_manager(user.email())
    if regio_manager:
        return regio_manager_has_permissions_to_team(regio_manager, team_id)
    logging.error("has_permissions_to_team failed for user '%s' and team '%s'", user, team_id)
    return False


@returns(bool)
@arguments(regio_manager=RegioManager, team_id=(int, long))
def regio_manager_has_permissions_to_team(regio_manager, team_id):
    return regio_manager.team_id == team_id if regio_manager else False


@returns(bool)
@arguments(user=users.User, question=Question)
def user_has_permissions_to_question(user, question):
    if is_admin(user):
        return True

    key = RegioManager.create_key(user.email())
    manager = RegioManager.get(key)
    if manager:
        if manager.admin and manager.team_id == question.team_id:
            return True

    return False
