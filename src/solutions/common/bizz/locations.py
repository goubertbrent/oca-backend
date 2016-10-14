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

from rogerthat.consts import FAST_QUEUE
from rogerthat.rpc import users
from rogerthat.service.api import system
from rogerthat.utils.transactions import on_trans_committed
from google.appengine.ext import db, deferred
from mcfw.rpc import returns, arguments
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import common_provision
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionIdentitySettings


@returns()
@arguments(service_user=users.User, name=unicode, broadcast_to_users=[users.User])
def create_new_location(service_user, name, broadcast_to_users=None):
    sln_settings = get_solution_settings(service_user)
    if sln_settings.identities:
        service_identity = int(max(sln_settings.identities)) + 1
    else:
        service_identity = 1
    service_identity = u"%s" % service_identity

    def trans():
        sln_i_settings_key = SolutionIdentitySettings.create_key(service_user, service_identity)
        sln_i_settings = SolutionIdentitySettings(key=sln_i_settings_key)
        sln_i_settings.name = name
        sln_i_settings.phone_number = sln_settings.phone_number
        sln_i_settings.qualified_identifier = sln_settings.qualified_identifier
        sln_i_settings.description = sln_settings.description
        sln_i_settings.opening_hours = sln_settings.opening_hours
        sln_i_settings.address = sln_settings.address
        sln_i_settings.location = sln_settings.location
        sln_i_settings.search_keywords = sln_settings.search_keywords
        sln_i_settings.inbox_forwarders = []
        sln_i_settings.inbox_connector_qrcode = None
        sln_i_settings.inbox_mail_forwarders = []
        sln_i_settings.inbox_email_reminders_enabled = False
        sln_i_settings.holidays = []
        sln_i_settings.holiday_out_of_office_message = common_translate(sln_settings.main_language, SOLUTION_COMMON, 'holiday-out-of-office')
        sln_i_settings.put()

        if not sln_settings.identities:
            sln_settings.identities = []
        sln_settings.identities.append(service_identity)
        sln_settings.put()
        on_trans_committed(_create_service_identity, service_user, sln_i_settings, broadcast_to_users)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)

@returns()
@arguments(service_user=users.User, sln_i_settings=SolutionIdentitySettings, broadcast_to_users=[users.User])
def _create_service_identity(service_user, sln_i_settings, broadcast_to_users=None):

    users.set_user(service_user)
    try:
        si_details = system.get_identity()

        si_details.identifier = sln_i_settings.service_identity
        si_details.name = sln_i_settings.name
        si_details.app_ids_use_default = True
        # the other info will be completed during provision
        system.put_identity(si_details)
        deferred.defer(common_provision, service_user, broadcast_to_users=broadcast_to_users, _queue=FAST_QUEUE)
    finally:
        users.clear_user()
