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

from google.appengine.ext import db, deferred, ndb

from mcfw.rpc import returns, arguments
from rogerthat.consts import FAST_QUEUE
from rogerthat.models import OpeningHours, ServiceIdentity
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.service.api import system
from rogerthat.utils.transactions import on_trans_committed
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
        sln_i_settings.inbox_forwarders = []
        sln_i_settings.inbox_connector_qrcode = None
        sln_i_settings.inbox_mail_forwarders = []
        sln_i_settings.inbox_email_reminders_enabled = False
        sln_i_settings.put()

        if not sln_settings.identities:
            sln_settings.identities = []
        sln_settings.identities.append(service_identity)
        sln_settings.put()
        _copy_service_info(service_user, service_identity, name)
        on_trans_committed(_create_service_identity, service_user, sln_i_settings, broadcast_to_users)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


def _copy_service_info(service_user, new_identity, name):
    hours = OpeningHours.create_key(service_user, ServiceIdentity.DEFAULT).get()  # type: OpeningHours
    if not hours:
        return
    new_hours = OpeningHours(key=OpeningHours.create_key(service_user, new_identity))
    new_hours.exceptional_opening_hours = hours.exceptional_opening_hours
    new_hours.periods = hours.periods
    new_hours.text = hours.text
    new_hours.type = hours.type
    new_hours.title = hours.title

    service_info = ServiceInfo.create_key(service_user, ServiceIdentity.DEFAULT).get()  # type: ServiceInfo
    info = ServiceInfo(key=ServiceInfo.create_key(service_user, new_identity))
    info.addresses = service_info.addresses
    info.cover_media = service_info.cover_media
    info.description = service_info.description
    info.email_addresses = service_info.email_addresses
    info.keywords = service_info.keywords
    info.name = name
    info.phone_numbers = service_info.phone_numbers
    info.place_types = service_info.place_types
    info.synced_fields = service_info.synced_fields
    info.timezone = service_info.timezone
    info.visible = service_info.visible
    info.websites = service_info.websites
    ndb.put_multi([new_hours, info])


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
