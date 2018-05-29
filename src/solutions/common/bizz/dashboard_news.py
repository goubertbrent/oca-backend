# -*- coding: utf-8 -*-
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
# @@license_version:1.4@@

from mcfw.exceptions import HttpNotFoundException
from mcfw.rpc import arguments
from solutions.common.models.news import DashboardNews
from solutions.common.to.news import DashboardNewsTO


def get_all_dashboard_news():
    return DashboardNews.query()


def get_dashboard_news_by_language(language):
    return DashboardNews.list_by_language(language)


def get_dashboard_news(news_id):
    # type: (long) -> DashboardNews
    model = DashboardNews.create_key(news_id).get()
    if not model:
        raise HttpNotFoundException('dashboard_news_not_found', {'id': news_id})
    return model


@arguments(data=DashboardNewsTO)
def create_dashboard_news(data):
    # type: (DashboardNewsTO) -> DashboardNews
    dashboard_news = DashboardNews(**data.to_dict())
    dashboard_news.put()
    return dashboard_news


@arguments(news_id=(int, long), data=DashboardNewsTO)
def update_dashboard_news(news_id, data):
    # type: (int, DashboardNewsTO) -> DashboardNews
    dashboard_news = get_dashboard_news(news_id)
    dashboard_news.populate(**data.to_dict(exclude=['id']))
    dashboard_news.put()
    return dashboard_news


def delete_dashboard_news(news_id):
    DashboardNews.create_key(news_id).delete()
