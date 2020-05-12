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

import cgi
from cStringIO import StringIO

from google.appengine.ext import db, ndb

from rogerthat.bizz.job import run_job
from rogerthat.rpc import users
from solutions.common.bizz.images import upload_file
from solutions.common.models import SolutionBrandingSettings, SolutionSettings


class BaseSolutionImage(db.Model):
    picture = db.BlobProperty()
    is_default = db.BooleanProperty(indexed=False, default=False)

    @property
    def service_user(self):
        return users.User(self.key().name())

    @classmethod
    def create_key(cls, service_user):
        return db.Key.from_path(cls.kind(), service_user.email())


class SolutionLogo(BaseSolutionImage):
    pass


class SolutionAvatar(BaseSolutionImage):
    published = db.BooleanProperty(indexed=False)


def migrate_1():
    run_job(_get_all_solution_settings, [], _1_create_images, [])


def migrate_2():
    run_job(_get_all_solution_settings, [], _2_delete_old_images, [])


def _get_all_solution_settings():
    return SolutionSettings.all(keys_only=True)


def _1_create_images(sln_settings_key):
    service_user = users.User(sln_settings_key.name())
    logo_key = SolutionLogo.create_key(service_user)
    avatar_key = SolutionAvatar.create_key(service_user)
    settings_key = SolutionBrandingSettings.create_key(service_user)
    logo, avatar, branding_settings = db.get((logo_key, avatar_key, settings_key)
                                             )  # type: (SolutionLogo, SolutionAvatar, SolutionBrandingSettings)
    ref = ndb.Key.from_old_key(branding_settings.key())
    if not logo or logo.is_default:
        branding_settings.logo_url = None
    else:
        file_ = cgi.FieldStorage(StringIO(logo.picture), {'content-type': 'image/png'})
        uploaded_file = upload_file(logo.service_user, file_, 'branding/logo', ref)
        branding_settings.logo_url = uploaded_file.url
    if not avatar or avatar.is_default:
        branding_settings.avatar_url = None
    else:
        file_ = cgi.FieldStorage(StringIO(avatar.picture), {'content-type': 'image/png'})
        uploaded_file = upload_file(logo.service_user, file_, 'branding/avatar', ref)
        branding_settings.avatar_url = uploaded_file.url
    db.put(branding_settings)


def _2_delete_old_images(sln_settings_key):
    # Split up into 2 migrations in case something went wrong
    service_user = users.User(sln_settings_key.name())
    logo_key = SolutionLogo.create_key(service_user)
    avatar_key = SolutionAvatar.create_key(service_user)
    db.delete([logo_key, avatar_key])
