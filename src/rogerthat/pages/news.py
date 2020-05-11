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

import httplib
import json

import webapp2

from mcfw.rpc import serialize_complex_value
from rogerthat.bizz.news import get_news_read_statistics
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
        news_ids = map(int, self.request.GET.get('news_ids', []).split(','))
        data = serialize_complex_value(get_news_read_statistics(news_ids), NewsReadInfoTO, True)
        json.dump(data, self.response.out)
