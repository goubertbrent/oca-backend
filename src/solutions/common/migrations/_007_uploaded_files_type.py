# -*- coding: utf-8 -*-
# Copyright 2021 Green Valley NV
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
from google.appengine.ext.ndb.model import get_multi, put_multi
from typing import List

from rogerthat.bizz.job import MODE_BATCH, run_job
from rogerthat.models.news import MediaType
from solutions.common.models.forms import UploadedFile


def migrate():
    run_job(_get_all, [], _migrate_uploaded_file, [], mode=MODE_BATCH, batch_size=50)


def _get_all():
    return UploadedFile.query()


content_type_mapping = {
    'image/jpeg': MediaType.IMAGE,
    'image/png': MediaType.IMAGE,
    'application/pdf': MediaType.PDF,
}


def _migrate_uploaded_file(keys):
    models = get_multi(keys)  # type: List[UploadedFile]
    to_put = []
    for model in models:
        if not model.type:
            model.type = content_type_mapping.get(model.content_type)
            if not model.type:
                raise Exception('Cannot guess file type based on content type: %s' % model)
            to_put.append(model)
    put_multi(to_put)
