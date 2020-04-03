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

from HTMLParser import HTMLParser
import hashlib
import logging
from types import NoneType
import urlparse

from google.appengine.api import urlfetch, images
from google.appengine.ext import ndb
from html5lib.sanitizer import HTMLSanitizerMixin

from mcfw.rpc import arguments, returns
from rogerthat.consts import DEBUG
from rogerthat.dal.service import get_default_service_identity
from rogerthat.models.news import NewsItem, MediaType
from rogerthat.rpc import users
from rogerthat.service.api import news
from rogerthat.to.news import NewsActionButtonTO, BaseMediaTO, NewsFeedNameTO
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.models import SolutionSettings
from solutions.common.utils import limit_string


BROADCAST_TYPE_NEWS = u"News"


def transl(key, language):
    try:
        return common_translate(language, SOLUTION_COMMON, key, suppress_warning=True)
    except:
        return key


def get_full_url(base_url, potential_partial_url):
    if not potential_partial_url:
        return potential_partial_url
    if potential_partial_url.startswith("http://") or potential_partial_url.startswith("https://"):
        return potential_partial_url

    parsed_base_url = urlparse.urlparse(base_url)
    return '%s://%s%s' % (parsed_base_url.scheme, parsed_base_url.netloc, potential_partial_url)


@returns()
@arguments(sln_settings=SolutionSettings, group_type=unicode, message=unicode, title=unicode, permalink=unicode,
           image_url=unicode, notify=bool, item_key=ndb.Key, app_ids=[unicode], feed_name=unicode, timestamp=(NoneType, int ,long))
def create_news_item(sln_settings, group_type, message, title, permalink, notify=False, image_url=None,
                     item_key=None, app_ids=None, feed_name=None, timestamp=None):
    service_user = sln_settings.service_user
    logging.info('Creating news item:\n- %s\n- %s\n- %s\n- %s\n- %s - %s - Notification: %s', service_user, message,
                 title, group_type, permalink, image_url, notify)

    with users.set_user(service_user):
        link_caption = transl(u'More info', sln_settings.main_language)
        action_button = NewsActionButtonTO(u'url', link_caption, permalink)
        si = get_default_service_identity(service_user)
        news_app_ids = app_ids if app_ids else si.appIds

        if feed_name:
            feed_names = []
            for app_id in news_app_ids:
                feed_names.append(NewsFeedNameTO(app_id, feed_name))
        else:
            feed_names = None

        title = limit_string(title, NewsItem.MAX_TITLE_LENGTH)
        flags = NewsItem.DEFAULT_FLAGS
        if not notify:
            flags = flags | NewsItem.FLAG_SILENT
        news_item = news.publish(sticky=False,
                                 sticky_until=0,
                                 title=title,
                                 message=message,
                                 news_type=NewsItem.TYPE_NORMAL,
                                 flags=flags,
                                 group_type=group_type,
                                 action_buttons=[action_button],
                                 qr_code_content=None,
                                 qr_code_caption=None,
                                 scheduled_at=0,
                                 app_ids=news_app_ids,
                                 feed_names=feed_names,
                                 media=_get_media(get_full_url(permalink, image_url)),
                                 timestamp=timestamp,
                                 accept_missing=True)
        if item_key:
            scraped_item = item_key.get()
            scraped_item.news_id = news_item.id
            scraped_item.put()


@returns()
@arguments(news_id=(int, long), sln_settings=SolutionSettings, group_type=unicode, message=unicode, title=unicode,
           permalink=unicode, image_url=unicode)
def update_news_item(news_id, sln_settings, group_type, message, title, permalink, image_url):
    service_user = sln_settings.service_user
    logging.info('Updating news item:\n- %s\n- %s\n- %s\n- %s\n - %s', service_user, message, title, group_type,
                 permalink)

    with users.set_user(service_user):
        link_caption = transl(u'More info', sln_settings.main_language)
        action_button = NewsActionButtonTO(u'url', link_caption, permalink)

        title = limit_string(title, NewsItem.MAX_TITLE_LENGTH)
        existing_item = news.get(news_id)
        news.publish(sticky=existing_item.sticky,
                     sticky_until=existing_item.sticky_until,
                     title=title,
                     message=message,
                     news_type=existing_item.type,
                     flags=existing_item.flags,
                     group_type=group_type,
                     action_buttons=[action_button],
                     scheduled_at=0,
                     app_ids=existing_item.app_ids,
                     news_id=news_id,
                     media=_get_media(get_full_url(permalink, image_url)),
                     accept_missing=True)


def _get_media(image_url):
    if not image_url:
        return None
    result = urlfetch.fetch(image_url, deadline=10)  # type: urlfetch._URLFetchResult
    if result.status_code != 200:
        return None

    decoded_image = result.content
    try:
        img = images.Image(decoded_image)
        orig_width = img.width
        orig_height = img.height
    except:
        logging.warn('Failed to get media for %s', image_url, exc_info=True)
        return None
    aspect_ratio = float(orig_width) / float(orig_height)
    if aspect_ratio > 3 or aspect_ratio < 1.0 / 3.0:
        return None

    # TODO: maybe copy to gcloud storage for better perf
    return BaseMediaTO(type=MediaType.IMAGE, content=image_url)


@arguments(news_id=(int, long), service_user=users.User)
def delete_news_item(news_id, service_user):
    with users.set_user(service_user):
        news.delete(news_id)


def news_item_hash(title, message, image_url):
    msg = u'%s%s%s' % (title, message, image_url or '')
    return hashlib.sha256(msg.encode('utf-8')).hexdigest()


def html_unescape(s):
    return HTMLParser().unescape(s)


def linestrip(s):
    return '\n'.join((line.strip() for line in s.splitlines()))


class TestIsHTMLParser(HTMLParser):

    def __init__(self, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)
        self.elements = set()

    def handle_starttag(self, tag, attrs):
        self.elements.add(tag)

    def handle_endtag(self, tag):
        self.elements.add(tag)


def is_html(text):
    try:
        elements = set(HTMLSanitizerMixin.acceptable_elements)
        parser = TestIsHTMLParser()
        parser.feed(text)
        return_value = True if parser.elements.intersection(elements) else False
#         if DEBUG:
#             logging.debug('is_html:%s elements: %s', return_value, parser.elements)
        return return_value
    except:
        logging.exception('Failed to determine if text was html')
    return True  # behaviour before this was always expect it was html
