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

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.rpc import users
from rogerthat.rpc.models import TempBlob
from rogerthat.utils import now
from rogerthat.utils.zip_utils import replace_file_in_zip_blob
from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred
from solutions.common.bizz import common_provision
from solutions.common.dal import get_solution_logo, get_solution_main_branding, get_solution_settings
from solutions.djmatic.models import DjMaticProfile


def job():
    resp = urlfetch.fetch('https://mobicage.dj-matic.com/default_template.zip', deadline=60)
    if resp.status_code != 200:
        raise Exception()

    b = TempBlob(key_name="fix_djmatic_brandings", blob=resp.content, timeout=now() + 86400)
    b.put()
    run_job(_get_djmatic_profiles, [], fix_brandings, [], worker_queue=MIGRATION_QUEUE)


def _get_djmatic_profiles():
    return DjMaticProfile.all(keys_only=True)


def fix_brandings(djmatic_profile_key):
    tmp_blob = TempBlob.get_by_key_name("fix_djmatic_brandings")
    service_user = users.User(djmatic_profile_key.parent().name())
    logo = get_solution_logo(service_user)
    if logo:
        zip_content = replace_file_in_zip_blob(tmp_blob.blob, "logo.jpg", str(logo.picture))
    else:
        zip_content = tmp_blob.blob

    def trans():
        sln_main_branding = get_solution_main_branding(service_user)
        sln_main_branding.blob = db.Blob(zip_content)
        sln_main_branding.branding_creation_time = 0

        common_settings = get_solution_settings(service_user)
        common_settings.updates_pending = True

        put_and_invalidate_cache(sln_main_branding, common_settings)
        deferred.defer(common_provision, service_user, _transactional=True)
        return common_settings

    xg_on = db.create_transaction_options(xg=True)
    users.set_user(service_user)
    try:
        db.run_in_transaction_options(xg_on, trans)
    finally:
        users.clear_user()
