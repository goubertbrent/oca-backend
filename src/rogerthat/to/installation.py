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

import warnings

from mcfw.properties import unicode_property, long_property, typed_property
from rogerthat.to import TO, PaginatedResultTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.to.system import MobileTO


class InstallationLogTO(TO):
    description = unicode_property('description')
    pin = long_property('pin')
    timestamp = long_property('timestamp')

    @staticmethod
    def from_model(model):
        return InstallationLogTO(description=model.description,
                                 pin=model.pin,
                                 timestamp=model.timestamp)


class InstallationTO(TO):
    id = unicode_property('id')
    version = unicode_property('version')
    platform = unicode_property('platform')
    timestamp = long_property('timestamp')
    app_id = unicode_property('app_id')
    status = unicode_property('status')
    mobile = typed_property('mobile', MobileTO)
    user_details = typed_property('user_details', UserDetailsTO)

    @classmethod
    def from_model(cls, model, mobile=None, profile=None):
        return cls(id=model.id,
                   version=model.version,
                   platform=model.platform_string,
                   timestamp=model.timestamp,
                   app_id=model.app_id,
                   status=model.status,
                   mobile=MobileTO.from_model(mobile) if mobile else None,
                   user_details=UserDetailsTO.fromUserProfile(profile) if profile else None)


class DeprecatedInstallationTO(InstallationTO):
    logs = typed_property('7', InstallationLogTO, True)

    @classmethod
    def from_model(cls, model, mobile, profile, logs=None):
        warnings.warn('Use InstallationTO instead', DeprecationWarning)
        to = super(DeprecatedInstallationTO, cls).from_model(model, mobile, profile)
        to.logs = [InstallationLogTO.from_model(log) for log in logs or []]
        return to


class DeprecatedInstallationsTO(TO):
    offset = long_property('1')
    cursor = unicode_property('2')
    installations = typed_property('3', DeprecatedInstallationTO, True)

    @classmethod
    def from_model(cls, offset, cursor, installations, logs_per_installation, mobiles, profiles):
        warnings.warn('Use InstallationListTO instead', DeprecationWarning)
        installations_to = []
        for installation in installations:
            installations_to.append(DeprecatedInstallationTO.from_model(installation,
                                                                        mobiles.get(installation.key()),
                                                                        profiles.get(installation.key()),
                                                                        logs_per_installation.get(installation.key())))
        return cls(offset=offset, cursor=cursor, installations=installations_to)


class InstallationListTO(PaginatedResultTO):
    results = typed_property('results', InstallationTO, True)

    @classmethod
    def from_query(cls, models, cursor, more, mobiles, profiles):
        results = [InstallationTO.from_model(model, mobiles.get(model.key()), profiles.get(model.key())) for model in
                   models]
        return cls(cursor=cursor, more=more, results=results)
