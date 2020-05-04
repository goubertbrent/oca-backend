# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

import logging
import uuid

from mcfw.rpc import returns, arguments
from rogerthat.models import ServiceMenuDef
from rogerthat.models.settings import SyncedNameValue
from rogerthat.rpc import users
from rogerthat.service.api import system
from rogerthat.to.messaging import BaseMemberTO
from rogerthat.utils.transactions import allow_transaction_propagation, run_in_xg_transaction
from solutions import translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import create_or_update_solution_service, SolutionModule, OrganizationType
from solutions.common.bizz.messaging import POKE_TAG_EVENTS, POKE_TAG_APPOINTMENT, POKE_TAG_ASK_QUESTION, \
    POKE_TAG_GROUP_PURCHASE, POKE_TAG_MENU, POKE_TAG_REPAIR, POKE_TAG_SANDWICH_BAR, POKE_TAG_WHEN_WHERE, \
    POKE_TAG_RESERVE_PART1, POKE_TAG_MY_RESERVATIONS, POKE_TAG_ORDER, POKE_TAG_PHARMACY_ORDER, \
    POKE_TAG_LOYALTY, POKE_TAG_DISCUSSION_GROUPS, POKE_TAG_BROADCAST_CREATE_NEWS, POKE_TAG_Q_MATIC, \
    POKE_TAG_JCC_APPOINTMENTS
from solutions.common.bizz.provisioning import get_and_complete_solution_settings, \
    get_and_store_main_branding, populate_identity, provision_all_modules, get_default_language
from solutions.common.dal import get_solution_settings
from solutions.common.models.associations import AssociationStatistic
from solutions.common.to import ProvisionResponseTO
from solutions.flex import SOLUTION_FLEX

# [column, row, page]
DEFAULT_COORDS = {
    SolutionModule.AGENDA: {
        POKE_TAG_EVENTS: {
            "preferred_page": 0,
            "coords": [0, 2, 0],
            "priority": 10
        },
    },
    SolutionModule.APPOINTMENT: {
        POKE_TAG_APPOINTMENT: {
            "preferred_page": 0,
            "coords": [-1, -1, -1],
            "priority": 5
        }
    },
    SolutionModule.ASK_QUESTION: {
        POKE_TAG_ASK_QUESTION: {
            "preferred_page": 0,
            "coords": [1, 1, 0],
            "priority": 20
        }
    },
    SolutionModule.BILLING: None,
    SolutionModule.BROADCAST: {
        ServiceMenuDef.TAG_MC_BROADCAST_SETTINGS: {
            "preferred_page": 0,
            "coords": [3, 2, 0],
            "priority": 20
        },
        POKE_TAG_BROADCAST_CREATE_NEWS: {
            "preferred_page": -1,
            "coords": [-1, -1, -1],
            "priority": 1
        }
    },
    SolutionModule.BULK_INVITE: None,
    SolutionModule.CITY_APP: None,
    SolutionModule.CITY_VOUCHERS: None,
    SolutionModule.DISCUSSION_GROUPS: {
        POKE_TAG_DISCUSSION_GROUPS: {
            "preferred_page": 0,
            "coords": [-1, -1, -1],
            "priority": 5
        }
    },
    SolutionModule.GROUP_PURCHASE: {
        POKE_TAG_GROUP_PURCHASE: {
            "preferred_page": 0,
            "coords": [-1, -1, -1],
            "priority": 5
        }
    },
    SolutionModule.LOYALTY: {
        POKE_TAG_LOYALTY: {
            "preferred_page": 0,
            "coords": [3, 1, 0],
            "priority": 10
        }
    },
    SolutionModule.MENU: {
        POKE_TAG_MENU: {
            "preferred_page": 0,
            "coords": [2, 1, 0],
            "priority": 10
        }
    },
    SolutionModule.ORDER: {
        POKE_TAG_ORDER: {
            "preferred_page": 0,
            "coords": [-1, -1, -1],
            "priority": 5
        }
    },
    SolutionModule.PHARMACY_ORDER: {
        POKE_TAG_PHARMACY_ORDER: {
            "preferred_page": 0,
            "coords": [-1, -1, -1],
            "priority": 5
        }
    },
    SolutionModule.QR_CODES: None,
    SolutionModule.REPAIR: {
        POKE_TAG_REPAIR: {
            "preferred_page": 0,
            "coords": [-1, -1, -1],
            "priority": 5
        }
    },
    SolutionModule.RESTAURANT_RESERVATION: {
        POKE_TAG_RESERVE_PART1: {
            "preferred_page": 0,
            "coords": [1, 2, 0],
            "priority": 5
        },
        POKE_TAG_MY_RESERVATIONS: {
            "preferred_page": 0,
            "coords": [2, 2, 0],
            "priority": 5
        }
    },
    SolutionModule.SANDWICH_BAR: {
        POKE_TAG_SANDWICH_BAR: {
            "preferred_page": 0,
            "coords": [3, 1, 0],
            "priority": 10
        }
    },
    SolutionModule.STATIC_CONTENT: None,
    SolutionModule.WHEN_WHERE: {
        POKE_TAG_WHEN_WHERE: {
            "preferred_page": 0,
            "coords": [0, 1, 0],
            "priority": 20
        }
    },
    SolutionModule.JOBS: None,

    SolutionModule.HIDDEN_CITY_WIDE_LOTTERY: None,

    SolutionModule.FORMS: None,
    SolutionModule.PARTICIPATION: None,
    SolutionModule.REPORTS: None,
    SolutionModule.Q_MATIC: {
        POKE_TAG_Q_MATIC: {
            'preferred_page': 0,
            'coords': [-1, -1, -1],
            'priority': 5,
        }
    },
    SolutionModule.JCC_APPOINTMENTS: {
        POKE_TAG_JCC_APPOINTMENTS: {
            'preferred_page': 0,
            'coords': [-1, -1, -1],
            'priority': 5,
        }
    },
    SolutionModule.CIRKLO_VOUCHERS: None
}


@returns(tuple)
@arguments(service_user=users.User, friends=[BaseMemberTO], transactional=bool)
def provision(service_user, friends=None, transactional=True):
    needs_reload = False
    with users.set_user(service_user):
        default_lang = get_default_language()
        sln_settings = get_and_complete_solution_settings(service_user, SOLUTION_FLEX)
        main_branding = get_and_store_main_branding(service_user)

        if sln_settings.modules_to_put or sln_settings.modules_to_remove:
            needs_reload = True
            for module in sln_settings.modules_to_put:
                if module not in sln_settings.modules:
                    sln_settings.modules.append(module)
            for module in sln_settings.modules_to_remove:
                if module in sln_settings.modules:
                    sln_settings.modules.remove(module)
            sln_settings.modules_to_put = []
            sln_settings.modules_to_remove = []

        for i, label in enumerate(['About', 'History', 'Call', 'Recommend']):
            system.put_reserved_menu_item_label(i, translate(sln_settings.main_language, SOLUTION_COMMON, label))

        if transactional:
            sln_settings = allow_transaction_propagation(run_in_xg_transaction, provision_all_modules, sln_settings,
                                                         DEFAULT_COORDS, main_branding, default_lang)
        else:
            sln_settings = provision_all_modules(sln_settings, DEFAULT_COORDS, main_branding, default_lang)

        populate_identity(sln_settings, main_branding.branding_key)

        system.publish_changes(friends)
        logging.info('Service populated!')
    return needs_reload, sln_settings


@returns(ProvisionResponseTO)
@arguments(email=unicode, name=unicode, phone_number=unicode, languages=[unicode], currency=unicode,
           modules=[unicode], broadcast_types=[unicode], apps=[unicode], allow_redeploy=bool, organization_type=int,
           search_enabled=bool, broadcast_to_users=[users.User], websites=[SyncedNameValue])
def create_flex_service(email, name, phone_number, languages, currency, modules, broadcast_types, apps,
                        allow_redeploy, organization_type=OrganizationType.PROFIT, search_enabled=False,
                        broadcast_to_users=None, websites=None):
    from rogerthat.bizz.rtemail import EMAIL_REGEX

    redeploy = allow_redeploy and get_solution_settings(users.User(email)) is not None
    branding_url = menu_item_color = None

    owner_user_email = None
    service_email = email
    if not redeploy and EMAIL_REGEX.match(service_email):
        owner_user_email = service_email
        service_email = u"service-%s@rogerth.at" % uuid.uuid4()

    return create_or_update_solution_service(SOLUTION_FLEX, service_email, name, branding_url, menu_item_color,
                                             phone_number, languages, currency, redeploy, organization_type, modules,
                                             broadcast_types, apps, owner_user_email=owner_user_email,
                                             search_enabled=search_enabled, broadcast_to_users=broadcast_to_users,
                                             websites=websites)


@returns(AssociationStatistic)
@arguments(app_id=unicode)
def get_services_statistics(app_id):
    return AssociationStatistic.get(AssociationStatistic.create_key(app_id))
