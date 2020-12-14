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

import logging

from rogerthat.bizz.job import run_job
from rogerthat.bizz.service import publish_changes, delete_menu_item
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal.service import get_service_menu_items
from solutions.common.bizz import SolutionModule
from solutions.common.bizz.messaging import POKE_TAG_EVENTS, POKE_TAG_APPOINTMENT, POKE_TAG_ASK_QUESTION, \
    POKE_TAG_DISCUSSION_GROUPS, POKE_TAG_GROUP_PURCHASE, POKE_TAG_LOYALTY, POKE_TAG_MENU, POKE_TAG_ORDER, \
    POKE_TAG_PHARMACY_ORDER, POKE_TAG_REPAIR, POKE_TAG_SANDWICH_BAR, POKE_TAG_WHEN_WHERE, POKE_TAG_RESERVE_PART1, \
    POKE_TAG_MY_RESERVATIONS
from solutions.common.models import SolutionSettings

REVERSE_POKE_TAG_MAPPING = {
    POKE_TAG_EVENTS: SolutionModule.AGENDA,
    POKE_TAG_APPOINTMENT: SolutionModule.APPOINTMENT,
    POKE_TAG_ASK_QUESTION: SolutionModule.ASK_QUESTION,
    POKE_TAG_DISCUSSION_GROUPS: SolutionModule.DISCUSSION_GROUPS,
    POKE_TAG_GROUP_PURCHASE: SolutionModule.GROUP_PURCHASE,
    POKE_TAG_LOYALTY: SolutionModule.LOYALTY,
    POKE_TAG_MENU: SolutionModule.MENU,
    POKE_TAG_MY_RESERVATIONS: SolutionModule.RESTAURANT_RESERVATION,
    POKE_TAG_ORDER: SolutionModule.ORDER,
    POKE_TAG_PHARMACY_ORDER: SolutionModule.PHARMACY_ORDER,
    POKE_TAG_REPAIR: SolutionModule.REPAIR,
    POKE_TAG_RESERVE_PART1: SolutionModule.RESTAURANT_RESERVATION,
    POKE_TAG_SANDWICH_BAR: SolutionModule.SANDWICH_BAR,
    POKE_TAG_WHEN_WHERE: SolutionModule.WHEN_WHERE,
}


def fix_services_with_excess_menu_items():
    run_job(_get_users, [], fix_service, [], worker_queue=MIGRATION_QUEUE)


def _get_users():
    return SolutionSettings.all(keys_only=True).order('-last_publish')


def fix_service(sln_settings_key):
    sln_settings = SolutionSettings.get(sln_settings_key)
    items = get_service_menu_items(sln_settings.service_user)  # type: list[ServiceMenuDef]
    deleted = []
    for item in items:
        if item.tag and item.tag in REVERSE_POKE_TAG_MAPPING:
            module = REVERSE_POKE_TAG_MAPPING[item.tag]
            if module not in sln_settings.modules and module not in sln_settings.modules_to_remove:
                deleted.append(module)
                delete_menu_item(sln_settings.service_user, item.coords)
    if deleted:
        logging.info('Deleted modules %s for user %s', deleted, sln_settings.service_user)
        publish_changes(sln_settings.service_user)
