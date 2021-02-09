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
import logging

from rogerthat.bizz.job import run_job
from rogerthat.consts import DEBUG
from rogerthat.models.settings import ServiceInfo, MediaItem
from solutions.common.models.forms import UploadedFile


def migrate():
    run_job(qry, [], _change_service_info_media, [])


def qry():
    return ServiceInfo.query()


def _change_service_info_media(key):
    info = key.get()  # type: ServiceInfo
    uploaded_files = {f.url: f for f in UploadedFile.list_by_user(info.service_user)}
    info.media = []
    for cover_media in info.cover_media:
        item = cover_media.item
        if item.content in uploaded_files:
            file_model = uploaded_files[item.content]
            info.media.append(MediaItem.from_file_model(file_model))
            continue
        if '/services' in item.content:
            logging.warning('UploadedFile not found: Service %s; file %s', info.service_user, item.content)
            if DEBUG:
                raise Exception('Expected to find file in uploaded files: %s' % item.content)
        info.media.append(MediaItem(type=item.type, content=item.content, thumbnail_url=item.thumbnail_url))
    info.put()
