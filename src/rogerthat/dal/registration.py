# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
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
# @@license_version:1.6@@

from google.appengine.ext import db

from mcfw.rpc import returns, arguments
from rogerthat.models import Registration, InstallationLog, Installation
from rogerthat.rpc.models import Mobile


@returns(Registration)
@arguments(mobile=Mobile)
def get_registration_by_mobile(mobile):
    return Registration.list_by_mobile(mobile).get()

@returns(tuple)
@arguments(min_timestamp=int, max_timestamp=int, cursor=unicode, batch_size=(int, long))
def get_installations(min_timestamp, max_timestamp, cursor=None, batch_size=10):
    qry = Installation.gql("WHERE timestamp > :min_timestamp AND timestamp < :max_timestamp ORDER BY timestamp DESC")
    qry.bind(min_timestamp=min_timestamp, max_timestamp=max_timestamp)
    qry.with_cursor(cursor)
    installations = qry.fetch(batch_size)
    return installations, qry.cursor()


@returns(tuple)
@arguments(app_id=unicode, cursor=unicode, page_size=(int, long))
def list_installations_by_app(app_id, cursor, page_size):
    qry = Installation.list_by_app(app_id).with_cursor(cursor)
    return qry.fetch(page_size), qry.cursor(), len(qry.with_cursor(qry.cursor()).fetch(1, keys_only=True)) == 1


@returns(tuple)
@arguments(installations=[Installation])
def get_mobiles_and_profiles_for_installations(installations):
    # get_value_for_datastore returns a key instead of the model itself. This way we can fetch all mobiles / profiles
    # in one datastore api call instead of synchronously fetching them per Installation model
    mobile_keys = {
        installation.key(): Installation.mobile.get_value_for_datastore(installation) for
        installation in installations if Installation.mobile.get_value_for_datastore(installation)}
    mobiles = {installation_key: mobile for installation_key, mobile in zip(mobile_keys, db.get(mobile_keys.values()))}
    profile_keys = {
        installation.key(): Installation.profile.get_value_for_datastore(installation) for
        installation in installations if Installation.profile.get_value_for_datastore(installation)}
    profiles = {installation_key: mobile for installation_key, mobile in
                zip(profile_keys, db.get(profile_keys.values()))}
    return mobiles, profiles


@returns([InstallationLog])
@arguments(installation=Installation)
def get_installation_logs_by_installation(installation):
    return InstallationLog.list_by_installation(installation)


@returns(Registration)
@arguments(installation=Installation)
def get_last_but_one_registration(installation):
    qry = Registration.gql("WHERE installation = :installation ORDER BY timestamp DESC OFFSET 1")
    qry.bind(installation=installation)
    return qry.get()
