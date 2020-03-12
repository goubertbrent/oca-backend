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
from datetime import datetime
from urlparse import urlparse

import PyRSS2Gen
from dateutil.parser import parse as parse_datetime
from google.appengine.api import urlfetch
from typing import List
from webapp2 import RequestHandler

from mcfw.exceptions import HttpException
from mcfw.rpc import arguments, returns


class RssCoronavirusDotBeHandler(RequestHandler):
    def get(self):
        url = self.request.params.get('url', 'https://www.info-coronavirus.be/nl/news')
        self.response.headers['Content-Type'] = 'application/rss+xml'
        self.response.out.write(get_coronavirus_dot_be_rss(url))


@returns(unicode)
@arguments(url=unicode)
def get_coronavirus_dot_be_rss(url):
    from bs4 import BeautifulSoup, Tag
    parsed_url = urlparse(url)
    base_url = '%s://%s' % (parsed_url.scheme, parsed_url.netloc)
    fetch_result = urlfetch.fetch(url)  # type: urlfetch._URLFetchResult
    if fetch_result.status_code != 200:
        raise HttpException.from_urlfetchresult(fetch_result)
    soup = BeautifulSoup(fetch_result.content, features='lxml')
    articles = soup.find_all('div', {'class': 'post-teaser'})  # type: List[Tag]
    items = []
    for article in articles:
        title = article.find('h3')  # type: Tag
        link_tag = article.find('a', {'class': 'read-more'})  # type: Tag
        description = '\n'.join(tag.text.strip() for tag in article.find_all('p'))
        date_tag = article.find('span', {'class': 'blue'})
        pub_date = parse_datetime(date_tag.text)
        link = link_tag.attrs['href']
        if link.startswith('/'):
            link = base_url + link
        items.append(PyRSS2Gen.RSSItem(
            title=title.text.strip(),
            link=link,
            description=description,
            pubDate=pub_date,
        ))
    rss = PyRSS2Gen.RSS2(
        title=soup.find('title').text.strip(),
        link=soup.find('meta', {'name': 'description'}).attrs['content'],
        description=soup.find('meta', {'name': 'description'}).attrs['content'],
        lastBuildDate=datetime.utcnow(),
        items=items)
    return rss.to_xml('utf-8')
