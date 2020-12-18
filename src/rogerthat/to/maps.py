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

from typing import List, Union  # @UnusedImport

from mcfw.properties import unicode_property, typed_property, long_property, \
    bool_property, unicode_list_property, object_factory, float_property
from mcfw.utils import Enum
from rogerthat.to import TO, GeoPointTO
from rogerthat.to.news import BaseMediaTO, SizeTO, GetNewsStreamFilterTO, NewsStreamItemTO
from rogerthat.to.system import ProfileAddressTO


class LatLonTO(TO):
    lat = float_property('lat')
    lon = float_property('lon')


class MapButtonTO(TO):
    action = unicode_property('action')
    color = unicode_property('color', default=None)
    icon = unicode_property('icon', default=None)
    text = unicode_property('text', default=None)
    service = unicode_property('service', default=None)


class MapConfigTO(TO):
    center = typed_property('center', LatLonTO, default=None)  # type: LatLonTO
    distance = long_property('distance', default=0)
    filters = unicode_list_property('filters', default=[])
    default_filter = unicode_property('default_filter', default=None)
    buttons = typed_property('buttons', MapButtonTO, True, default=[])

    @classmethod
    def from_model(cls, m):
        to = MapConfigTO()
        if m:
            to.center = LatLonTO(lat=m.center.lat, lon=m.center.lon)
            to.distance = m.distance
            to.filters = m.filters
            to.default_filter = m.default_filter
            to.buttons = m.buttons
        else:
            to.center = LatLonTO(lat=51.0974612, lon=3.8378242)
            to.distance = 7287
            to.max_distance = 15000
        return to



class MapFilterTO(TO):
    key = unicode_property('1')
    label = unicode_property('2')


class MapGeometryType(object):
    LINE_STRING = 'LineString'
    MULTI_LINE_STRING = 'MultiLineString'
    POLYGON = 'Polygon'
    MULTI_POLYGON = 'MultiPolygon'


class CoordsListTO(TO):
    coords = typed_property('coords', GeoPointTO, True)


class PolygonTO(TO):
    rings = typed_property('rings', CoordsListTO, True)


class LineStringGeometryTO(TO):
    type = unicode_property('type', default=MapGeometryType.LINE_STRING)
    color = unicode_property('color')
    line = typed_property('line', CoordsListTO, False)


class MultiLineStringGeometryTO(TO):
    type = unicode_property('type', default=MapGeometryType.MULTI_LINE_STRING)
    color = unicode_property('color')
    lines = typed_property('lines', CoordsListTO, True)


class PolygonGeometryTO(PolygonTO):
    type = unicode_property('type', default=MapGeometryType.POLYGON)
    color = unicode_property('color')


class MultiPolygonGeometryTO(TO):
    type = unicode_property('type', default=MapGeometryType.MULTI_POLYGON)
    color = unicode_property('color')
    polygons = typed_property('polygons', PolygonTO, True)


MAP_GEOMETRY_MAPPING = {
    MapGeometryType.LINE_STRING: LineStringGeometryTO,
    MapGeometryType.MULTI_LINE_STRING: MultiLineStringGeometryTO,
    MapGeometryType.POLYGON: PolygonGeometryTO,
    MapGeometryType.MULTI_POLYGON: MultiPolygonGeometryTO,
}


class MapGeometryTO(object_factory):
    type = unicode_property('type')
    color = unicode_property('color')

    def __init__(self):
        super(MapGeometryTO, self).__init__('type', MAP_GEOMETRY_MAPPING, MapGeometryType)


class MapListSectionItemType(object):
    TOGGLE = 'toggle'
    LINK = 'link'
    OPENING_HOURS = 'opening_hours'  # deprecated - do not use
    DYNAMIC_OPENING_HOURS = 'opening-hours'
    EXPANDABLE = 'expandable'


class BaseListSectionItem(TO):
    icon = unicode_property('icon')
    icon_color = unicode_property('icon_color', default=None)
    title = unicode_property('title')  # markdown


class ToggleListSectionItemTO(BaseListSectionItem):
    TOGGLE_ID_SAVE = u'save'
    type = unicode_property('type', default=MapListSectionItemType.TOGGLE)
    id = unicode_property('id')
    state = unicode_property('state')
    filled = bool_property('filled')


class HorizontalLinkListItemStyle(Enum):
    ROUND_BUTTON_WITH_ICON = 0


class VerticalLinkListItemStyle(Enum):
    DEFAULT = 0
    BUTTON = 1


class LinkListSectionItemTO(BaseListSectionItem):
    type = unicode_property('type', default=MapListSectionItemType.LINK)
    url = unicode_property('url')
    external = bool_property('external', default=False)
    style = long_property('style', default=VerticalLinkListItemStyle.DEFAULT)
    request_user_link = bool_property('request_user_link', default=False)


class ExpandableListSectionItemTO(BaseListSectionItem):
    type = unicode_property('type', default=MapListSectionItemType.EXPANDABLE)


class MapItemLineTextPartTO(TO):
    color = unicode_property('color', default=None)
    text = unicode_property('text')

    def __eq__(self, other):
        if not other or not isinstance(other, MapItemLineTextPartTO):
            return False
        return self.color == other.color \
            and self.text == other.text


class WeekDayTextTO(TO):
    day = unicode_property('day')
    lines = typed_property('lines', MapItemLineTextPartTO, True)

    def __eq__(self, other):
        if not other or not isinstance(other, WeekDayTextTO):
            return False
        return self.day == other.day \
            and self.lines == other.lines


class OpeningHourTO(TO):
    day = long_property('day')
    time = unicode_property('time')


class OpeningPeriodTO(TO):
    open = typed_property('open', OpeningHourTO)  # type: OpeningHourTO
    close = typed_property('close', OpeningHourTO)  # type: OpeningHourTO
    description = unicode_property('description', default=None)
    description_color = unicode_property('description_color', default=None)


class OpeningHourExceptionTO(TO):
    start_date = unicode_property('start_date')
    end_date = unicode_property('end_date')
    description = unicode_property('description')
    description_color = unicode_property('description_color', default=None)
    periods = typed_property('periods', OpeningPeriodTO, True, default=[])  # type: List[OpeningPeriodTO]


class OpeningHoursTO(TO):
    id = unicode_property('id')
    type = unicode_property('type')
    text = unicode_property('text')
    title = unicode_property('title')
    periods = typed_property('periods', OpeningPeriodTO, True, default=[])  # type: List[OpeningPeriodTO]
    exceptional_opening_hours = typed_property('exceptional_opening_hours', OpeningHourExceptionTO,
                                               True, default=[])  # type: List[OpeningHourExceptionTO]


class OpeningInfoTO(TO):
    name = unicode_property('name')  # optional name in case there are opening hours for multiple locations
    title = unicode_property('title')  # opening soon, open, closing soon, closed, ...
    title_color = unicode_property('title_color', default=None)
    subtitle = unicode_property('subtitle')  # 11:00 AM - 8:00 PM etc
    description = unicode_property('description')  # Christmas Eve might affect these hours
    description_color = unicode_property('description_color', default=None)
    weekday_text = typed_property('weekday_text', WeekDayTextTO, True)


class OpeningHoursListSectionItemTO(BaseListSectionItem):
    type = unicode_property('type', default=MapListSectionItemType.OPENING_HOURS)
    opening_hours = typed_property('opening_hours', OpeningInfoTO)


class OpeningHoursSectionItemTO(BaseListSectionItem):
    type = unicode_property('type', default=MapListSectionItemType.DYNAMIC_OPENING_HOURS)
    timezone = unicode_property('timezone')
    opening_hours = typed_property('opening_hours', OpeningHoursTO)


MAP_LIST_SECTION_ITEM_MAPPING = {
    MapListSectionItemType.TOGGLE: ToggleListSectionItemTO,
    MapListSectionItemType.LINK: LinkListSectionItemTO,
    # deprecated - only here for backwards compat
    MapListSectionItemType.OPENING_HOURS: OpeningHoursListSectionItemTO,
    MapListSectionItemType.DYNAMIC_OPENING_HOURS: OpeningHoursSectionItemTO,
    MapListSectionItemType.EXPANDABLE: ExpandableListSectionItemTO,
}


class MapListSectionItemTO(object_factory):
    type = unicode_property('type')
    icon = unicode_property('icon')
    icon_color = unicode_property('icon_color')
    title = unicode_property('title')  # markdown

    def __init__(self):
        super(MapListSectionItemTO, self).__init__('type', MAP_LIST_SECTION_ITEM_MAPPING, MapListSectionItemType)


class MapSectionType(object):
    TEXT = 'text'
    GEOMETRY = 'geometry'
    VOTE = 'vote'
    LIST = 'list'
    MEDIA = 'media'
    NEWS = 'news'
    NEWS_GROUP = 'news-group'


class TextSectionTO(TO):
    type = unicode_property('type', default=MapSectionType.TEXT)
    title = unicode_property('title')
    description = unicode_property('description')


class GeometrySectionTO(TO):
    type = unicode_property('type', default=MapSectionType.GEOMETRY)
    title = unicode_property('title')
    description = unicode_property('description')
    geometry = typed_property('geometry', MapGeometryTO(), True)


class MapVoteOptionTO(TO):
    id = unicode_property('id')
    icon = unicode_property('icon')
    title = unicode_property('title')
    count = long_property('count')
    color = unicode_property('color')
    selected = bool_property('selected')


class VoteSectionTO(TO):
    type = unicode_property('type', default=MapSectionType.VOTE)
    id = unicode_property('id')
    options = typed_property('options', MapVoteOptionTO, True)


class ListSectionStyle(Enum):
    VERTICAL = u'vertical'
    HORIZONTAL = u'horizontal'


class ListSectionTO(TO):
    type = unicode_property('type', default=MapSectionType.LIST)
    style = unicode_property('style', default=ListSectionStyle.VERTICAL)
    items = typed_property('items', MapListSectionItemTO(), True)


class MediaSectionTO(TO):
    type = unicode_property('type', default=MapSectionType.MEDIA)
    ratio = typed_property('ratio', SizeTO, False)  # type: SizeTO
    items = typed_property('items', BaseMediaTO, True)  # type: List[BaseMediaTO]


class NewsSectionTO(TO):
    type = unicode_property('type', default=MapSectionType.NEWS)
    filter = typed_property('filter', GetNewsStreamFilterTO, False)
    limit = long_property('limit')
    placeholder_image = unicode_property('placeholder_image')

class NewsGroupSectionTO(TO):
    type = unicode_property('type', default=MapSectionType.NEWS_GROUP)
    filter = typed_property('filter', GetNewsStreamFilterTO)
    group_id = unicode_property('group_id')
    items = typed_property('items', NewsStreamItemTO, True)
    placeholder_image = unicode_property('placeholder_image')


MAP_SECTION_MAPPING = {
    MapSectionType.TEXT: TextSectionTO,
    MapSectionType.GEOMETRY: GeometrySectionTO,
    MapSectionType.VOTE: VoteSectionTO,
    MapSectionType.LIST: ListSectionTO,
    MapSectionType.MEDIA: MediaSectionTO,
    MapSectionType.NEWS: NewsSectionTO,
    MapSectionType.NEWS_GROUP: NewsGroupSectionTO,
}


class MapSectionTO(object_factory):
    type = unicode_property('type')

    def __init__(self):
        super(MapSectionTO, self).__init__('type', MAP_SECTION_MAPPING, MapSectionType)


MAP_SECTION_TYPES = Union[TextSectionTO, GeometrySectionTO, VoteSectionTO, ListSectionTO, MediaSectionTO,
                          NewsGroupSectionTO]


class MapIconTO(TO):
    id = unicode_property('1')
    color = unicode_property('2')


class MapAnnouncementType(object):
    TEXT = 'text'


class TextAnnouncementTO(TO):
    type = unicode_property('type', default=MapAnnouncementType.TEXT)
    title = unicode_property('title')
    description = unicode_property('description')


MAP_ANNOUNCEMENT_MAPPING = {
    MapAnnouncementType.TEXT: TextAnnouncementTO,
}

class MapAnnouncementTO(object_factory):
    type = unicode_property('type')

    def __init__(self):
        super(MapAnnouncementTO, self).__init__('type', MAP_ANNOUNCEMENT_MAPPING, MapAnnouncementType)


class MapActionChipType(object):
    SEARCH_SUGGESTION = 'search_suggestion'


class SearchSuggestionTO(TO):
    type = unicode_property('type', default=MapActionChipType.SEARCH_SUGGESTION)
    icon = unicode_property('icon')
    title = unicode_property('title')


MAP_ACTION_CHIP_MAPPING = {
    MapActionChipType.SEARCH_SUGGESTION: SearchSuggestionTO,
}


class MapActionChipTO(object_factory):
    type = unicode_property('type')

    def __init__(self):
        super(MapActionChipTO, self).__init__('type', MAP_ACTION_CHIP_MAPPING, MapActionChipType)


class MapItemLineType(object):
    TEXT = 'text'


class MapItemLineTextTO(TO):
    type = unicode_property('type', default=MapItemLineType.TEXT)
    parts = typed_property('parts', MapItemLineTextPartTO, True)


MAP_ITEM_LINE_MAPPING = {
    MapItemLineType.TEXT: MapItemLineTextTO,
}


class MapItemLineTO(object_factory):
    type = unicode_property('type')

    def __init__(self):
        super(MapItemLineTO, self).__init__('type', MAP_ITEM_LINE_MAPPING, MapItemLineType)


class MapItemTO(TO):
    id = unicode_property('id')
    coords = typed_property('coords', GeoPointTO, False)
    icon = typed_property('icon', MapIconTO, False)
    title = unicode_property('title')
    description = unicode_property('description')
    lines = typed_property('lines', MapItemLineTO(), True, default=[])


class MapItemDetailsTO(TO):
    id = unicode_property('id')
    geometry = typed_property('geometry', MapGeometryTO(), True)
    sections = typed_property('sections', MapSectionTO(), True)


class MapDefaultsTO(TO):
    filter = unicode_property('1', default=None)
    coords = typed_property('2', GeoPointTO, False)
    distance = long_property('3')
    max_distance = long_property('4')


class MapBaseUrlsTO(TO):
    icon_pin = unicode_property('1')
    icon_transparent = unicode_property('2')


class MapNotificationsTO(TO):
    enabled = bool_property('1')


class GetMapRequestTO(TO):
    tag = unicode_property('1')


class MapFunctionality(Enum):
    ADDRESSES = u'map.addresses'
    CURRENT_LOCATION = u'map.current_location'
    SEARCH = u'map.search'
    SAVE = u'map.save'
    AUTO_LOAD_DETAILS = u'map.items.auto_load_details'


class GetMapResponseTO(TO):
    functionalities = unicode_list_property('functionalities', default=[])
    defaults = typed_property('defaults', MapDefaultsTO, False)  # type: MapDefaultsTO
    filters = typed_property('filters', MapFilterTO, True)  # type: List[MapFilterTO]
    addresses = typed_property('addresses', ProfileAddressTO, True)  # type: List[ProfileAddressTO]
    notifications = typed_property('notifications', MapNotificationsTO, False)  # type: MapNotificationsTO
    base_urls = typed_property('base_urls', MapBaseUrlsTO, False)  # type: MapBaseUrlsTO
    title = unicode_property('title')
    empty_text = unicode_property('empty_text', default=None)
    buttons = typed_property('buttons', MapButtonTO, True, default=[])  # type: List[MapButtonTO]
    announcement = typed_property('announcement', MapAnnouncementTO(), False, default=None)
    action_chips = typed_property('action_chips', MapActionChipTO(), True, default=[])


class MapSearchTO(TO):
    query = unicode_property('query')


class MapSearchSuggestionType(object):
    KEYWORD = 'keyword'
    ITEM = 'item'


class MapSearchSuggestionKeywordTO(TO):
    type = unicode_property('type', default=MapSearchSuggestionType.KEYWORD)
    text = unicode_property('text')


class MapSearchSuggestionItemTO(TO):
    type = unicode_property('type', default=MapSearchSuggestionType.ITEM)
    id = unicode_property('id')
    text = unicode_property('text')


MAP_SEARCH_SUGGESTION_MAPPING = {
    MapSearchSuggestionType.KEYWORD: MapSearchSuggestionKeywordTO,
    MapSearchSuggestionType.ITEM: MapSearchSuggestionItemTO,
}


class MapSearchSuggestionTO(object_factory):
    type = unicode_property('type')

    def __init__(self):
        super(MapSearchSuggestionTO, self).__init__('type', MAP_SEARCH_SUGGESTION_MAPPING, MapSearchSuggestionType)


class GetMapSearchSuggestionsRequestTO(TO):
    tag = unicode_property('tag')
    filter = unicode_property('filter')
    coords = typed_property('coords', GeoPointTO, False)
    distance = long_property('distance')
    search = typed_property('search', MapSearchTO, False, default=None)


class GetMapSearchSuggestionsResponseTO(TO):
    items = typed_property('items', MapSearchSuggestionTO(), True)


class GetMapItemsRequestTO(TO):
    tag = unicode_property('tag')
    filter = unicode_property('filter')
    coords = typed_property('coords', GeoPointTO, False)
    distance = long_property('distance')
    cursor = unicode_property('cursor', default=None)
    search = typed_property('search', MapSearchTO, False, default=None)


class GetMapItemsResponseTO(TO):
    cursor = unicode_property('cursor')
    items = typed_property('items', MapItemTO, True)
    distance = long_property('distance')
    top_sections = typed_property('top_sections', MapSectionTO(), True, default=[])


class GetMapItemDetailsRequestTO(TO):
    tag = unicode_property('1')
    ids = unicode_list_property('2')


class GetMapItemDetailsResponseTO(TO):
    items = typed_property('1', MapItemDetailsTO, True)


class SaveMapNotificationsRequestTO(TO):
    tag = unicode_property('1')
    notifications = typed_property('2', MapNotificationsTO, False)


class SaveMapNotificationsResponseTO(TO):
    message = unicode_property('message')
    notifications = typed_property('notifications', MapNotificationsTO)


class ToggleMapItemRequestTO(TO):
    tag = unicode_property('tag')
    item_id = unicode_property('item_id')
    toggle_id = unicode_property('toggle_id')
    state = unicode_property('state')


class ToggleMapItemResponseTO(TO):
    item_id = unicode_property('item_id')
    toggle_item = typed_property('toggle_item', ToggleListSectionItemTO)


class GetSavedMapItemsRequestTO(TO):
    tag = unicode_property('tag')
    cursor = unicode_property('cursor', default=None)


class GetSavedMapItemsResponseTO(TO):
    cursor = unicode_property('cursor')
    items = typed_property('items', MapItemTO, True)


class SaveMapItemVoteRequestTO(TO):
    tag = unicode_property('tag')
    item_id = unicode_property('item_id')
    vote_id = unicode_property('vote_id')
    option_id = unicode_property('option_id')


class SaveMapItemVoteResponseTO(TO):
    item_id = unicode_property('item_id')
    vote_id = unicode_property('vote_id')
    options = typed_property('options', MapVoteOptionTO, True)
