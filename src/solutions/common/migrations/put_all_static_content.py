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

from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal import parent_key
from rogerthat.utils.transactions import run_in_transaction
from solutions import SOLUTION_COMMON
from solutions.common.models.static_content import SolutionStaticContent


def job():
    deferred.defer(put_all_static_content, _queue=MIGRATION_QUEUE)


def put_all_static_content(cursor=None):
    qry = SolutionStaticContent.all()
    qry.with_cursor(cursor)
    models = qry.fetch(200)
    new_models = list()
    if not models:
        return
    for m in models:
        tmp = m.key().name().split("x", 2)
        coords = [int(tmp[1]), int(tmp[2]), int(tmp[0])]
        new_model = SolutionStaticContent(parent=parent_key(m.service_user, SOLUTION_COMMON),
                                          coords=coords,
                                          old_coords=coords,
                                          sc_type=m.sc_type,
                                          icon_label=m.icon_label,
                                          icon_name=m.icon_name,
                                          text_color=m.text_color,
                                          background_color=m.background_color,
                                          html_content=m.html_content,
                                          branding_hash=m.branding_hash,
                                          visible=True,
                                          provisioned=True,
                                          deleted=False)
        new_models.append(new_model)

    def trans():
        db.put(new_models)
        db.delete(models)

    run_in_transaction(trans, True)
    deferred.defer(put_all_static_content, qry.cursor(), _queue=MIGRATION_QUEUE)
