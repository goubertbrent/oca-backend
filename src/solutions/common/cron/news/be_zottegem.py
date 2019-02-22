# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import logging
from xml.dom import minidom

from google.appengine.api import urlfetch
from google.appengine.ext.deferred import deferred

from solutions.common.cron.news import html_to_markdown
from solutions.common.cron.news.NewsScraper import NewsScraper


class BeZottegemNewsScraper(NewsScraper):
    BASE_URL = 'http://zottegem.be'

    def __init__(self, service_user):
        super(BeZottegemNewsScraper, self).__init__(service_user)

    def check_for_news(self):
        url = u'%s/systems/rss.aspx?pg=1164' % self.BASE_URL
        response = urlfetch.fetch(url, deadline=60)
        if response.status_code != 200:
            logging.error('Could not check for news in be-oudenaarde.\n%s', response.content)
            return

        doc = minidom.parseString(response.content)
        for item in doc.getElementsByTagName('item'):
            title = u'%s' % item.getElementsByTagName('title')[0].firstChild.nodeValue
            content_html = u'%s' % item.getElementsByTagName('content')[0].firstChild.nodeValue
            description_html = item.getElementsByTagName('description')[0].firstChild.nodeValue
            permalink = u'%s' % item.getElementsByTagName('link')[0].firstChild.nodeValue
            content = html_to_markdown(content_html)
            description = html_to_markdown(description_html)
            if len(description) > len(content):
                message = description
            else:
                message = content
            message = message.replace('[%MEDIA%]', '')
            deferred.defer(self.create_news, self.broadcast_type, title, message, permalink)


def check_for_news(service_user):
    deferred.defer(_check_for_news, service_user)

def _check_for_news(service_user):
    BeZottegemNewsScraper(service_user).check_for_news()
