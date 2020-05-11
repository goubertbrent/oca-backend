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

from google.appengine.api import images
from google.appengine.ext import ndb

from rogerthat.bizz.job import run_job
from rogerthat.models.news import NewsItem, NewsMedia, NewsItemImage, MediaType


def migrate():
    run_job(_get_news_items, [], _save_news_item, [])


def migrate2():
    run_job(_get_news_items, [], _set_deleted, [])


def _get_news_items():
    return NewsItem.query()


@ndb.transactional(xg=True)
def _save_news_item(key):
    news_item = key.get()  # type: NewsItem
    if news_item.image_id:
        image = NewsItemImage.create_key(news_item.image_id).get()
        img = images.Image(image.image)
        news_item.media = NewsMedia(type=MediaType.IMAGE, content=news_item.image_id, width=img.width,
                                    height=img.height)
    del news_item.image_id
    news_item.put()


@ndb.transactional(xg=True)
def _set_deleted(key):
    news_item = key.get()  # type: NewsItem
    news_item.deleted = False
    news_item.put()
