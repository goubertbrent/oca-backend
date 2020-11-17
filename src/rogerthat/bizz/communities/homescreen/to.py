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
from mcfw.properties import object_factory, unicode_property, typed_property, long_property, bool_property
from rogerthat.to import TO
from rogerthat.to.maps import MapSectionType, MapListSectionItemType, ListSectionStyle, VerticalLinkListItemStyle
from rogerthat.to.news import GetNewsStreamFilterTO


class HomeScreenSectionType(object):
    TEXT = MapSectionType.TEXT
    LIST = MapSectionType.LIST
    NEWS = MapSectionType.NEWS


class BottomSheetListItemType(object):
    OPENING_HOURS = MapListSectionItemType.DYNAMIC_OPENING_HOURS
    EXPANDABLE = MapListSectionItemType.EXPANDABLE
    LINK = MapListSectionItemType.LINK


class ExpandableItemSource(object):
    NONE = 0
    SERVICE_INFO_DESCRIPTION = 1


class LinkItemSource(object):
    NONE = 0
    SERVICE_INFO_PHONE = 1
    SERVICE_INFO_EMAIL = 2
    SERVICE_INFO_WEBSITE = 3
    SERVICE_INFO_ADDRESS = 4
    SERVICE_MENU_ITEM = 5


class OpeningHoursItemTemplate(TO):
    type = unicode_property('type', default=BottomSheetListItemType.OPENING_HOURS)


class ExpandableItemTemplate(TO):
    type = unicode_property('type', default=BottomSheetListItemType.EXPANDABLE)
    # in case of ExpandableItemSource.NONE, icon and title must be set
    source = long_property('source', default=ExpandableItemSource.NONE)
    icon = unicode_property('icon')
    title = unicode_property('title')  # markdown


class LinkItemContentDefault(TO):
    source = long_property('source', default=LinkItemSource.NONE)
    url = unicode_property('url', default=None)
    external = bool_property('external', default=False)
    request_user_link = bool_property('request_user_link', default=False)


class LinkItemSyncedContent(TO):
    source = long_property('source')
    index = long_property('index', default=0)


class LinkItemAddress(TO):
    source = long_property('source', default=LinkItemSource.SERVICE_INFO_ADDRESS)


class LinkItemServiceMenuItem(TO):
    source = long_property('source', default=LinkItemSource.SERVICE_MENU_ITEM)
    service = unicode_property('service')
    tag = unicode_property('tag')


LINK_ITEM_CONTENT_MAPPING = {
    LinkItemSource.NONE: LinkItemContentDefault,
    LinkItemSource.SERVICE_INFO_PHONE: LinkItemSyncedContent,
    LinkItemSource.SERVICE_INFO_EMAIL: LinkItemSyncedContent,
    LinkItemSource.SERVICE_INFO_WEBSITE: LinkItemSyncedContent,
    LinkItemSource.SERVICE_INFO_ADDRESS: LinkItemAddress,
    LinkItemSource.SERVICE_MENU_ITEM: LinkItemServiceMenuItem,
}


class LinkItemContent(object_factory):
    source = long_property('source')

    def __init__(self):
        super(LinkItemContent, self).__init__('source', LINK_ITEM_CONTENT_MAPPING, LinkItemSource)


class LinkItemTemplate(TO):
    type = unicode_property('type', default=BottomSheetListItemType.LINK)
    content = typed_property('content', LinkItemContent())
    style = long_property('style', default=VerticalLinkListItemStyle.DEFAULT)
    title = unicode_property('title', default=None)  # markdown
    icon = unicode_property('icon')
    icon_color = unicode_property('icon_color', default=None)


BOTTOM_SHEET_ITEM_MAPPING = {
    BottomSheetListItemType.OPENING_HOURS: OpeningHoursItemTemplate,
    BottomSheetListItemType.EXPANDABLE: ExpandableItemTemplate,
    BottomSheetListItemType.LINK: LinkItemTemplate,
}


class BottomSheetListItemTemplate(object_factory):
    type = unicode_property('type')

    def __init__(self):
        super(BottomSheetListItemTemplate, self).__init__('type', BOTTOM_SHEET_ITEM_MAPPING, BottomSheetListItemType)


class TextSectionTemplate(TO):
    type = unicode_property('type', default=HomeScreenSectionType.TEXT)
    title = unicode_property('title')
    description = unicode_property('description', default=None)


class ListSectionTemplate(TO):
    type = unicode_property('type', default=HomeScreenSectionType.LIST)
    style = unicode_property('style', default=ListSectionStyle.VERTICAL)
    items = typed_property('items', BottomSheetListItemTemplate(), True)


class NewsSectionTemplate(TO):
    type = unicode_property('type', default=HomeScreenSectionType.NEWS)
    filter = typed_property('filter', GetNewsStreamFilterTO)
    limit = long_property('limit')


BOTTOM_SHEET_SECTION_MAPPING = {
    HomeScreenSectionType.TEXT: TextSectionTemplate,
    HomeScreenSectionType.LIST: ListSectionTemplate,
    HomeScreenSectionType.NEWS: NewsSectionTemplate,
}


class BottomSheetSectionTemplate(object_factory):
    type = unicode_property('type')

    def __init__(self):
        super(BottomSheetSectionTemplate, self).__init__('type', BOTTOM_SHEET_SECTION_MAPPING, HomeScreenSectionType)


BottomSheetSectionTemplateInstance = BottomSheetSectionTemplate()


class TestHomeScreenTO(TO):
    test_user = unicode_property('test_user')
