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

import base64

import cloudstorage
from google.appengine.ext import ndb
from google.appengine.ext.deferred import deferred
from typing import List

from mcfw.consts import MISSING
from mcfw.exceptions import HttpNotFoundException, HttpBadRequestException
from mcfw.rpc import arguments, returns
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.communities.models import Community
from rogerthat.bizz.gcs import upload_to_gcs
from rogerthat.bizz.job import run_job
from rogerthat.bizz.system import update_embedded_apps_response, update_embedded_app_response
from rogerthat.capi.system import updateEmbeddedApps, updateEmbeddedApp
from rogerthat.consts import GCS_BUCKET_PREFIX, DAY, SCHEDULED_QUEUE
from rogerthat.models import UserProfile
from rogerthat.models.apps import EmbeddedApplication
from rogerthat.rpc import users
from rogerthat.rpc.rpc import logError
from rogerthat.to.app import CreateEmbeddedApplicationTO, UpdateEmbeddedApplicationTO, UpdateEmbeddedAppsRequestTO, \
    EmbeddedAppTO, UpdateEmbeddedAppRequestTO


class EmbeddedApplicationNotFoundException(HttpNotFoundException):
    def __init__(self, name):
        super(EmbeddedApplicationNotFoundException, self).__init__('embedded_application_not_found', {'name': name})


class EmbeddedApplicationNameAlreadyInUseException(HttpBadRequestException):

    def __init__(self, name):
        super(EmbeddedApplicationNameAlreadyInUseException, self).__init__('embedded_application_name_already_in_use',
                                                                           {'name': name})


class EmbeddedApplicationStillInUseException(HttpBadRequestException):

    def __init__(self, name, community_ids):
        super(EmbeddedApplicationStillInUseException, self).__init__('embedded_application_still_in_use',
                                                                     {'name': name,
                                                                      'community_ids': community_ids})


def get_embedded_applications(tag=None):
    # type: (unicode) -> list[EmbeddedApplication]
    if tag:
        qry = EmbeddedApplication.list_by_tag(tag)
    else:
        qry = EmbeddedApplication.query()
    return qry.fetch()


def get_embedded_application(name):
    # type: (unicode) -> EmbeddedApplication
    app = EmbeddedApplication.get_by_id(name)
    if not app:
        raise EmbeddedApplicationNotFoundException(name)
    return app


def _upload_file(data, name, version):
    # type: (str, unicode, int) -> str
    _, zip_str = data.split(',')
    decoded_zip = base64.b64decode(zip_str)
    content_type = 'application/octet-stream'
    file_name = '/%s/embedded-apps/%s-%d.zip' % (GCS_BUCKET_PREFIX, name, version)
    upload_to_gcs(decoded_zip, content_type, file_name)
    return file_name


def check_if_exists(name):
    if EmbeddedApplication.create_key(name).get() is not None:
        raise EmbeddedApplicationNameAlreadyInUseException(name)


@returns(EmbeddedApplication)
@arguments(data=CreateEmbeddedApplicationTO)
def create_embedded_application(data):
    check_if_exists(data.name)
    file_path = _upload_file(data.file, data.name, 1)

    app = EmbeddedApplication(key=EmbeddedApplication.create_key(data.name),
                              tags=data.tags,
                              file_path=file_path,
                              url_regexes=data.url_regexes,
                              title=data.title,
                              description=data.description,
                              types=data.types,
                              app_types=data.app_types)
    app.put()
    return app


@returns(EmbeddedApplication)
@arguments(name=unicode, data=UpdateEmbeddedApplicationTO)
def update_embedded_application(name, data):
    app = get_embedded_application(name)
    app.populate(tags=data.tags,
                 url_regexes=data.url_regexes,
                 title=data.title,
                 description=data.description,
                 types=data.types,
                 app_types=data.app_types,
                 version=app.version + 1)
    old_file_path = None
    if MISSING.default(data.file, None):
        old_file_path = app.file_path
        app.file_path = _upload_file(data.file, app.name, app.version)
    app.put()
    deferred.defer(send_update_embedded_app, name)
    if old_file_path:
        deferred.defer(cloudstorage.delete, old_file_path, _countdown=DAY, _queue=SCHEDULED_QUEUE)
    return app


def delete_embedded_application(name):
    community_ids = get_communities_that_use_embedded_app(name)
    if community_ids:
        raise EmbeddedApplicationStillInUseException(name, community_ids)

    application = get_embedded_application(name)
    if application.file_path:
        try:
            cloudstorage.delete(application.file_path)
        except cloudstorage.NotFoundError:
            pass
    application.key.delete()


@returns([EmbeddedApplication])
def get_embedded_apps_by_community(community_id):
    # type: (long) -> List[EmbeddedApplication]
    community = get_community(community_id)
    return ndb.get_multi([EmbeddedApplication.create_key(name) for name in community.embedded_apps])


@returns([EmbeddedApplication])
@arguments(embedded_app_type=unicode)
def get_embedded_apps_by_type(embedded_app_type):
    return EmbeddedApplication.list_by_type(embedded_app_type)


def get_communities_that_use_embedded_app(name):
    # type: (str) -> List[long]
    return [key.id() for key in Community.list_by_embedded_app(name).fetch(keys_only=True)]


def send_update_embedded_app(name):
    community_ids = get_communities_that_use_embedded_app(name)
    application = get_embedded_application(name)
    request = UpdateEmbeddedAppRequestTO.from_dict(application.to_dict())
    for community_id in community_ids:
        run_job(_get_users_by_community, [community_id], send_update_embedded_app_request_worker, [request])


def send_update_all_embedded_apps(community_id):
    embedded_apps = get_embedded_apps_by_community(community_id)
    request = UpdateEmbeddedAppsRequestTO(embedded_apps=[EmbeddedAppTO.from_model(a) for a in embedded_apps])
    run_job(_get_users_by_community, [community_id], send_update_embedded_apps_request_worker, [request])


def _get_users_by_community(community_id):
    return UserProfile.list_by_community(community_id, keys_only=True)


def send_update_embedded_app_request_worker(user_profile_key, request):
    app_user = users.User(user_profile_key.parent().name())
    updateEmbeddedApp(update_embedded_app_response, logError, app_user, request=request)


def send_update_embedded_apps_request_worker(user_profile_key, request):
    # type: (db.Key, UpdateEmbeddedAppsRequestTO) -> None
    app_user = users.User(user_profile_key.parent().name())
    updateEmbeddedApps(update_embedded_apps_response, logError, app_user, request=request)
