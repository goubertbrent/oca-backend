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

import httplib
import json

import webapp2

from rogerthat.bizz.news import get_news_by_ids
from rogerthat.consts import DAY
from rogerthat.models.news import NewsItemImage
from rogerthat.to.news import NewsReadInfoTO


class ViewNewsImageHandler(webapp2.RequestHandler):
    def get(self, image_id):
        try:
            image_id = long(image_id)
        except ValueError:
            self.error(httplib.NOT_FOUND)
            return
        image = NewsItemImage.get_by_id(image_id)
        if not image:
            self.error(httplib.NOT_FOUND)
            return
        self.response.cache_control = 'public'
        self.response.cache_expires(DAY * 30)
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.headers['Content-Disposition'] = 'inline; filename=%d.jpg' % image_id
        self.response.write(image.image)


class NewsSaveReadItems(webapp2.RequestHandler):
    def get(self):
        news_ids = []
        ids = self.request.GET.get('news_ids')
        if ids:
            news_ids = map(int, ids.split(','))
        news_items = get_news_by_ids(news_ids)
        result = [NewsReadInfoTO.from_news_model(news_item).to_dict() for news_item in news_items]
        json.dump(result, self.response.out)
