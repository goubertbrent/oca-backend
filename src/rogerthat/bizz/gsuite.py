# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
import json
import logging

import httplib2
from apiclient import discovery
from google.appengine.ext.deferred import deferred
from googleapiclient.errors import HttpError

# These scopes must be granted by delegated_user on this page
# https://admin.google.com/AdminHome?chromeless=1#OGX:ManageOauthClients
# the service account ( from gsuite_service_account) must have G Suite Domain-wide Delegation enabled
# See this page https://console.cloud.google.com/iam-admin/serviceaccounts/project
from solution_server_settings import get_solution_server_settings

SCOPES = ['https://www.googleapis.com/auth/admin.directory.group',
          'https://www.googleapis.com/auth/admin.directory.group.readonly',
          'https://www.googleapis.com/auth/admin.directory.group.member']


def _get_admin_directory_service():
    from oauth2client.service_account import ServiceAccountCredentials
    server_settings = get_solution_server_settings()
    account = json.loads(server_settings.gsuite_service_account)
    credentials = ServiceAccountCredentials._from_parsed_json_keyfile(account, SCOPES)\
        .create_delegated(server_settings.gsuite_delegated_user)
    http = credentials.authorize(httplib2.Http())
    return discovery.build('admin', 'directory_v1', http=http)


def create_app_group(app_id):
    email = '%s@%s' % (app_id, get_solution_server_settings().gsuite_domain)
    service = _get_admin_directory_service()
    try:
        group = service.groups().insert(body={'email': email, 'name': app_id}).execute()
        logging.info('Added new group %s', group)
        deferred.defer(_add_default_members_to_group, group['id'])
    except HttpError as e:
        if e.resp.status != 409:
            raise
        else:
            logging.info('No new group added, group for app_id %s already exists', app_id)


def _add_default_members_to_group(group_id):
    # Use batch requests if this is too slow https://developers.google.com/api-client-library/python/guide/batch
    service = _get_admin_directory_service()
    server_settings = get_solution_server_settings()
    members = json.loads(server_settings.default_email_group_members)
    for member in members:
        try:
            service.members().insert(groupKey=group_id, body=member).execute()
            logging.info('added %s to group with id %s', member, group_id)
        except HttpError as e:
            if e.resp.status != 409:
                raise
