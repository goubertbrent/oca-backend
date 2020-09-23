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
from cgi import FieldStorage

import cloudstorage

from mcfw.exceptions import HttpNotFoundException, HttpBadRequestException
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.consts import FILES_BUCKET
from rogerthat.models.news import NewsGroup, NewsGroupTile, NewsStream
from rogerthat.to.news import NewsGroupConfigTO, NewsSettingsTO, NewsSettingsWithGroupsTO
from rogerthat.utils import random_string, read_file_in_chunks


def get_news_settings(community_id):
    # type: (int) -> NewsSettingsWithGroupsTO
    stream = NewsStream.create_key(community_id).get()  # type: NewsStream
    groups = NewsGroup.list_by_community_id(community_id)
    return NewsSettingsWithGroupsTO(stream_type=stream.stream_type,
                                    groups=[NewsGroupConfigTO.from_model(m) for m in groups if not m.regional])


def update_news_stream(community_id, stream_type):
    stream = NewsStream.create_key(community_id).get()  # type: NewsStream
    stream.stream_type = stream_type
    stream.put()
    return NewsSettingsTO(stream_type=stream.stream_type)


def upload_news_background_image(community_id, group_id, uploaded_file):
    # type: (long, str, FieldStorage) -> NewsGroupConfigTO
    news_group = NewsGroup.create_key(group_id).get()
    if not news_group:
        raise HttpNotFoundException('oca.error', {'message': 'News group not found'})
    if community_id != news_group.community_id:
        raise HttpBadRequestException('oca.error', {'message': 'Invalid community id'})

    content_type = uploaded_file.type or 'image/jpeg'
    extension = '.jpg' if content_type == 'image/jpeg' else '.png'
    cloudstorage_path = '/%s/news/groups/%s/%s_%s%s' % (FILES_BUCKET, community_id, news_group.group_type,
                                                        random_string(5), extension)
    with cloudstorage.open(cloudstorage_path, 'w', content_type=content_type) as f:
        for chunk in read_file_in_chunks(uploaded_file.file):
            f.write(chunk)

    url = get_serving_url(cloudstorage_path)

    if not news_group.tile:
        news_group.tile = NewsGroupTile()
    news_group.tile.background_image_url = url
    news_group.put()

    return NewsGroupConfigTO.from_model(news_group)
