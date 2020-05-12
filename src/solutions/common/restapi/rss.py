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

from datetime import datetime
from urlparse import urlparse

import PyRSS2Gen
from dateutil.parser import parse as parse_datetime
from google.appengine.api import urlfetch
from typing import List
from webapp2 import RequestHandler

from mcfw.exceptions import HttpException
from mcfw.rpc import arguments, returns
from solutions.common.utils import html_to_markdown


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
    ul = soup.find('ul', {'class': 'blog-list'})
    articles = ul.find_all('li')  # type: List[Tag]
    items = []
    for article in articles:
        link_tag = article.find('a')  # type: Tag
        link = link_tag.attrs['href']
        if link.startswith('/'):
            link = base_url + link
        items.append(PyRSS2Gen.RSSItem(
            link=link,
            title=link_tag.text
        ))
        if len(items) >= 5:
            break
    rpcs = []
    for item in items:
        rpc = urlfetch.create_rpc(10)
        urlfetch.make_fetch_call(rpc, item.link)
        rpcs.append(rpc)
    for item, rpc in zip(items, rpcs):
        result = rpc.get_result()  # type: urlfetch._URLFetchResult
        if result.status_code != 200:
            raise HttpException.from_urlfetchresult(fetch_result)
        item_soup = BeautifulSoup(result.content, features='lxml')
        article = item_soup.find('article')
        item.pubDate = parse_datetime(article.find('time').attrs['datetime'])
        # Remove the header containing the title and date
        article.find('header').extract()
        item.description = html_to_markdown(unicode(article))
    rss = PyRSS2Gen.RSS2(
        title=soup.find('title').text.strip(),
        link=soup.find('meta', {'name': 'description'}).attrs['content'],
        description=soup.find('meta', {'name': 'description'}).attrs['content'],
        lastBuildDate=datetime.utcnow(),
        items=items)
    return rss.to_xml('utf-8')
