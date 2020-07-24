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
import json

from google.appengine.ext import ndb
from typing import Optional, Tuple, List

from mcfw.exceptions import HttpNotFoundException
from rogerthat.dal.app import get_app_by_id
from rogerthat.models import AppNameMapping, App
from rogerthat.models.news import NewsItem, MediaType
from rogerthat.rpc import users
from rogerthat.templates import JINJA_ENVIRONMENT
from rogerthat.to.news import NewsItemTO
from rogerthat.translations import localize, DEFAULT_LANGUAGE
from rogerthat.utils.service import remove_slash_default
from rogerthat.web_client.api.app import rest_get_app_info
from rogerthat.web_client.api.news import rest_get_news_item
from rogerthat.web_client.pages.web_client import WebRequestHandler
from solutions.common.dal import get_solution_settings


def _format_date(timestamp):
    # type: (int) -> str
    return datetime.utcfromtimestamp(timestamp).isoformat() + 'Z'


def get_app_tags(app):
    # type: (App) -> List[Tuple[str, str]]
    tags = [('google-play-app', 'app-id=' + app.android_app_id)]
    if app.ios_app_id != '-1':
        tags.append(('apple-itunes-app', 'app-id=' + app.ios_app_id))
    return tags


def get_meta_tags_for_news(news_item, url, locale, title, site_name):
    # type: (NewsItem, str, str, str, str) -> List[Tuple[str, str]]
    tags = [
        ('og:title', title),
        ('og:type', 'article'),
        ('og:url', url),
        ('og:description', '\n'.join(news_item.message.splitlines()[:3])),
        ('og:locale', locale),
        ('og:site_name', site_name),
        ('article:published_time', _format_date(news_item.published_timestamp)),
        ('article:modified_time', _format_date(news_item.update_timestamp)),
    ]
    if news_item.media:
        if news_item.media.type == MediaType.IMAGE:
            tags.extend([
                ('og:image', news_item.media.url),
                ('og:image:secure_url', news_item.media.url),
                ('og:image:width', news_item.media.width),
                ('og:image:height', news_item.media.height),

            ])
        elif news_item.media.type == MediaType.VIDEO_YOUTUBE:
            tags.extend([
                ('og:video', news_item.media.url),
                ('og:video:secure_url', news_item.media.url),
                ('og:video:width', news_item.media.width),
                ('og:video:height', news_item.media.height),
            ])
    return tags


def render_meta_tags(tags):
    items = ['<meta property="%s" content="%s" />' % tag for tag in sorted(tags)]
    return '\n'.join(items)


def render_web_page(language, tags, title, initial_state):
    from solutions.common.restapi import api_get_translations
    translations = {language: api_get_translations(language, prefix='web')}
    if language != DEFAULT_LANGUAGE:
        translations[DEFAULT_LANGUAGE] = api_get_translations(DEFAULT_LANGUAGE, prefix='web')
    js_globals = """<script>
    var oca = {
        mainLanguage: '%(language)s',
        translations: %(translations)s,
        initialState: %(initialState)s,
    }
</script>""" % {
        'language': language,
        'translations': json.dumps(translations),
        'initialState': json.dumps(initial_state)
    }
    return JINJA_ENVIRONMENT.get_template('web-app.html').render() \
        .replace('<!-- extra-meta -->', render_meta_tags(tags)) \
        .replace('<title></title>', '<title>%s</title>' % title) \
        .replace('<!-- custom-script-content -->', js_globals) \
        .replace('lang="en"', 'lang="%s"' % language)


def get_result_state_success(result):
    return {
        'state': 2,
        'result': result
    }


def get_default_initial_state(app_url_name):
    return {
        # RootState on the client
        'app': {
            'appInfo': get_result_state_success(rest_get_app_info(app_url_name))
        }
    }


def get_news_initial_state(news_item):
    # type: (NewsItemTO) -> dict
    return {
        # NewsState on the client
        'news': {
            'currentNewsItem': get_result_state_success(news_item.to_dict())
        }
    }


class NewsPageHandler(WebRequestHandler):

    def _render_page(self, application_identifier, news_id):
        news_id = long(news_id)
        language = self.get_language()
        try:
            news_item_to = rest_get_news_item(application_identifier, news_id, language=language)
        except HttpNotFoundException:
            # TODO fancy 404 page
            self.abort(404)
        models = ndb.get_multi([NewsItem.create_key(news_id), AppNameMapping.create_key(application_identifier)])
        news_item, app_mapping = models  # type: NewsItem, Optional[AppNameMapping]
        app = get_app_by_id(app_mapping.app_id)

        sln_settings = get_solution_settings(remove_slash_default(users.User(news_item_to.sender.email)))
        news_item_language = sln_settings.main_language

        site_name = localize(language, 'OCA')
        title = '%s - %s' % (news_item_to.title, site_name)
        tags = get_meta_tags_for_news(news_item, news_item_to.share_url, news_item_language, title, site_name)
        tags.extend(get_app_tags(app))

        initial_state = get_default_initial_state(application_identifier)
        initial_state.update(get_news_initial_state(news_item_to))
        self.response.out.write(render_web_page(language, tags, title, initial_state))

    def head(self, application_identifier, news_id):
        self._render_page(application_identifier, news_id)

    def get(self, application_identifier, news_id):
        super(NewsPageHandler, self).get(application_identifier, news_id)
        self._render_page(application_identifier, news_id)
