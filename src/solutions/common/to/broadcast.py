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

from mcfw.properties import unicode_property, typed_property, bool_property, long_property, unicode_list_property, \
    object_factory
from mcfw.utils import Enum
from rogerthat.to import TO
from rogerthat.to.news import ServiceNewsGroupTO, NewsActionButtonTO


class RegionalNewsSettingsTO(TO):
    enabled = bool_property('enabled')
    map_url = unicode_property('map_url')


class BaseNewsButtonTO(TO):
    label = unicode_property('label')
    button = typed_property('button', NewsActionButtonTO)
    icon = unicode_property('icon')


class NewsActionButtonType(Enum):
    WEBSITE = 0
    PHONE = 1
    EMAIL = 2
    ATTACHMENT = 3
    MENU_ITEM = 4
    OPEN = 5


class NewsActionButtonWebsite(BaseNewsButtonTO):
    type = long_property('type', default=NewsActionButtonType.WEBSITE)


class NewsActionButtonPhone(BaseNewsButtonTO):
    type = long_property('type', default=NewsActionButtonType.PHONE)
    phone = unicode_property('phone', default='')


class NewsActionButtonEmail(BaseNewsButtonTO):
    type = long_property('type', default=NewsActionButtonType.EMAIL)
    email = unicode_property('email', default='')


class NewsActionButtonAttachment(BaseNewsButtonTO):
    type = long_property('type', default=NewsActionButtonType.ATTACHMENT)


class NewsActionButtonMenuItem(BaseNewsButtonTO):
    type = long_property('type', default=NewsActionButtonType.MENU_ITEM)


class NewsActionButtonOpen(BaseNewsButtonTO):
    type = long_property('type', default=NewsActionButtonType.OPEN)


NEWS_ACTION_BUTTONS = {
    NewsActionButtonType.WEBSITE: NewsActionButtonWebsite,
    NewsActionButtonType.PHONE: NewsActionButtonPhone,
    NewsActionButtonType.EMAIL: NewsActionButtonEmail,
    NewsActionButtonType.ATTACHMENT: NewsActionButtonAttachment,
    NewsActionButtonType.MENU_ITEM: NewsActionButtonMenuItem,
    NewsActionButtonType.OPEN: NewsActionButtonOpen,
}


class DashboardNewsGroupTO(ServiceNewsGroupTO):
    regional_allowed = bool_property('regional_allowed')


class NewsActionButtonFactory(object_factory):
    type = long_property('type')

    def __init__(self):
        super(NewsActionButtonFactory, self).__init__('type', NEWS_ACTION_BUTTONS, NewsActionButtonType)


class NewsOptionsTO(TO):
    tags = unicode_list_property('tags')
    regional = typed_property('regional', RegionalNewsSettingsTO)
    groups = typed_property('groups', DashboardNewsGroupTO, True)
    media_types = unicode_list_property('media_types')
    location_filter_enabled = bool_property('location_filter_enabled')
    action_buttons = typed_property('action_buttons', NewsActionButtonFactory(), True)
    service_name = unicode_property('service_name')
    community_id = long_property('community_id')


class NewsCommunityTO(TO):
    id = long_property('id')
    name = unicode_property('name')
    total_user_count = long_property('total_user_count')

    @classmethod
    def from_model(cls, m, total_user_count):
        return NewsCommunityTO(id=m.id, name=m.name, total_user_count=total_user_count)
