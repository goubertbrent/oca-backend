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

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal import put_in_chunks
from rogerthat.models import Installation, InstallationLog, InstallationStatus


def migrate():
    run_job(_get_installations, [], _migrate_installation, [], worker_queue=MIGRATION_QUEUE)


def _get_installations():
    return Installation.all(keys_only=True).order('-timestamp')


def _migrate_installation(installation_key):
    installation = Installation.get(installation_key)
    to_put = [installation]
    installation.status = InstallationStatus.STARTED
    # Remove reference properties from installation logs and move them to the Installation model
    for log in InstallationLog.all().ancestor(installation):
        if log.description.capitalize().startswith('Registration successful'):
            installation.status = InstallationStatus.FINISHED
        elif installation.status != InstallationStatus.FINISHED:
            if 'pressed' in log.description or 'authorized' in log.description:
                installation.status = InstallationStatus.IN_PROGRESS
        if hasattr(log, 'mobile') and log.mobile:
            installation.mobile = log.mobile
        if hasattr(log, 'profile') and log.profile:
            installation.profile = log.profile
        attrs_to_delete = ['registration', 'mobile', 'profile', 'description_url']
        for attr in attrs_to_delete:
            if hasattr(log, attr):
                delattr(log, attr)
        to_put.append(log)
    put_in_chunks(to_put)
