# -*- coding: utf-8 -*-
# Copyright 2021 Green Valley NV
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
from __future__ import unicode_literals
import urllib

import logging

from google.appengine.ext import ndb
from typing import Optional, List

from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.models import CommunityMapSettings
from rogerthat.bizz.maps.poi.models import PointOfInterest
from rogerthat.bizz.maps.poi.search import _suggest_poi, search_poi
from rogerthat.bizz.maps.services import get_place_details, get_clean_language_code, ORGANIZATION_TYPE_SEARCH_PREFIX, \
    get_tags_app, SearchTag, PlaceDetails
from rogerthat.bizz.maps.shared import get_map_response
from rogerthat.bizz.opening_hours import get_opening_hours_lines
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import UserProfileInfo, OpeningHours
from rogerthat.models.news import MediaType
from rogerthat.rpc import users
from rogerthat.to import GeoPointTO
from rogerthat.to.maps import GetMapResponseTO, MapFunctionality, SearchSuggestionTO, MapBaseUrlsTO, \
    GetMapSearchSuggestionsResponseTO, GetMapSearchSuggestionsRequestTO, MapSearchSuggestionKeywordTO, \
    MapSearchSuggestionItemTO, GetMapItemsResponseTO, GetMapItemsRequestTO, GetMapItemDetailsResponseTO, \
    GetMapItemDetailsRequestTO, MapItemLineTextTO, MapItemLineTextPartTO, MapItemTO, MapIconTO, MediaSectionTO, \
    ListSectionTO, ListSectionStyle, LinkListSectionItemTO, ExpandableListSectionItemTO, OpeningHoursTO, \
    OpeningHoursSectionItemTO, MapItemDetailsTO, MapSearchTO
from rogerthat.to.news import BaseMediaTO, SizeTO
from rogerthat.translations import localize
from rogerthat.utils.app import get_app_id_from_app_user

POI_TAG = 'poi'


@returns(GetMapResponseTO)
@arguments(app_user=users.User)
def get_map(app_user):
    user_profile = get_user_profile(app_user)
    language = user_profile.language
    community_id = user_profile.community_id
    models = ndb.get_multi([CommunityMapSettings.create_key(community_id), UserProfileInfo.create_key(app_user)])
    map_config, user_profile_info = models  # type: CommunityMapSettings, UserProfileInfo
    map_config = map_config or CommunityMapSettings.get_default(community_id)
    response = get_map_response(map_config, POI_TAG, user_profile_info, [], add_addresses=False)
    response.functionalities = [MapFunctionality.CURRENT_LOCATION,
                                MapFunctionality.SEARCH]

    action_place_types = []
    response.action_chips = []
    for place_type in action_place_types:
        place_details = get_place_details(place_type, language)
        if not place_details:
            logging.warn('failed to use place_type:%s as action_chip details not found', place_type)
            continue
        if not place_details.fa_icon:
            logging.warn('failed to use place_type:%s as action_chip fa_icon not found', place_type)
            continue
        response.action_chips.append(SearchSuggestionTO(icon=place_details.fa_icon, title=place_details.title))

    response.base_urls = MapBaseUrlsTO(icon_pin='https://storage.googleapis.com/oca-files/map/icons/pin',
                                       icon_transparent='https://storage.googleapis.com/oca-files/map/icons/transparent')
    response.title = localize(language, 'services_around_you')
    response.empty_text = localize(language, 'no_services_at_location')
    return response


@returns(GetMapSearchSuggestionsResponseTO)
@arguments(app_user=users.User, request=GetMapSearchSuggestionsRequestTO)
def get_map_search_suggestions(app_user, request):
    from rogerthat.bizz.maps.services import _suggest_place_types

    response = GetMapSearchSuggestionsResponseTO(items=[])

    user_profile = get_user_profile(app_user)
    lang = user_profile.language

    suggestions = _suggest_place_types(request.search.query, get_clean_language_code(lang))
    for suggestion in suggestions:
        if suggestion.startswith(ORGANIZATION_TYPE_SEARCH_PREFIX):
            continue
        place_details = get_place_details(suggestion, lang)
        if not place_details:
            continue
        response.items.append(MapSearchSuggestionKeywordTO(text=place_details.title))

    app_id = get_app_id_from_app_user(app_user)
    app = get_app_by_id(app_id)
    tags, community_ids = get_tags_app(app)
    tags.append(SearchTag.visible_for_end_user())
    items = _suggest_poi(tags,
                         request.coords.lat,
                         request.coords.lon,
                         request.search.query,
                         community_ids)
    for poi in items:
        response.items.append(MapSearchSuggestionItemTO(id=poi['id'],
                                                        text=poi['name']))

    return response


@returns(GetMapItemsResponseTO)
@arguments(app_user=users.User, request=GetMapItemsRequestTO)
def get_map_items(app_user, request):
    from rogerthat.bizz.maps.services import _search_place_types_and_organization_types
    center_lat = request.coords.lat
    center_lon = request.coords.lon
    distance = request.distance

    app_id = get_app_id_from_app_user(app_user)
    app = get_app_by_id(app_id)
    tags, community_ids = get_tags_app(app)
    tags.append(SearchTag.visible_for_end_user())

    search_tags = []
    if request.search:
        user_profile = get_user_profile(app_user)
        lang = user_profile.language
        place_type_or_org_type = _search_place_types_and_organization_types(request.search.query,
                                                                            get_clean_language_code(lang))
        if place_type_or_org_type:
            if not place_type_or_org_type.startswith(ORGANIZATION_TYPE_SEARCH_PREFIX):
                search_tags = [SearchTag.place_type(place_type_or_org_type)]
    return _get_items(app_user, tags, search_tags, center_lat, center_lon, distance, cursor=request.cursor,
                      search=None if search_tags else request.search, community_ids=community_ids)


@returns(GetMapItemDetailsResponseTO)
@arguments(app_user=users.User, request=GetMapItemDetailsRequestTO)
def get_map_item_details(app_user, request):
    return GetMapItemDetailsResponseTO(items=_get_map_item_details_to_from_ids(app_user, request.ids))


def _get_items(app_user, tags, place_type_tags, lat, lon, distance, limit=100, cursor=None, search=None,
               community_ids=None):
    # type: (users.User, List[str], List[str], float, float, int, int, Optional[str], MapSearchTO, List[int]) -> GetMapItemsResponseTO
    if limit > 1000:
        limit = 1000
    new_cursor, result_ids = search_poi(tags, place_type_tags, lat, lon, distance, cursor, limit,
                                        search and search.query, community_ids)
    user_profile = get_user_profile(app_user)
    keys = [PointOfInterest.create_key(long(uid)) for uid in result_ids]
    poi_list = ndb.get_multi(keys)  # type: List[PointOfInterest]
    return GetMapItemsResponseTO(cursor=new_cursor,
                                 items=[_convert_to_item_to(item, user_profile.language) for item in poi_list if item],
                                 distance=distance,
                                 top_sections=[])


def _convert_to_item_to(poi_item, language):
    # type: (PointOfInterest, str) -> MapItemTO
    lines = []
    line_1 = []
    for place_type in poi_item.place_types:
        place_details = get_place_details(place_type, language)
        if not place_details:
            continue
        line_1.append(place_details.title)
    main_place_details = get_place_details(poi_item.main_place_type, language)
    if main_place_details:
        icon_id = main_place_details.png_icon
        icon_color = main_place_details.icon_color
    else:
        icon_id = PlaceDetails.png_icon.default
        icon_color = PlaceDetails.icon_color.default

    if line_1:
        lines.append(MapItemLineTextTO(parts=[MapItemLineTextPartTO(color=None, text=txt) for txt in line_1]))

    if poi_item.location.street:
        lines.append(
            MapItemLineTextTO(parts=[MapItemLineTextPartTO(color=None, text=poi_item.get_address_line(language))]))

    if poi_item.opening_hours:
        opening_hours_model = poi_item.opening_hours
        if opening_hours_model.type == OpeningHours.TYPE_STRUCTURED:
            lines.extend(get_opening_hours_lines(opening_hours_model, language, poi_item.location.timezone))

    return MapItemTO(id=unicode(poi_item.id),
                     coords=GeoPointTO(lat=poi_item.location.coordinates.lat,
                                       lon=poi_item.location.coordinates.lon),
                     icon=MapIconTO(id=icon_id,
                                    color=icon_color),
                     title=poi_item.title,
                     description=None,
                     lines=lines)


def _get_map_item_details_to_from_ids(app_user, ids):
    user_profile = get_user_profile(app_user)
    lang = user_profile.language
    map_items = []
    poi_list = ndb.get_multi([PointOfInterest.create_key(long(uid))
                              for uid in ids])  # type: List[PointOfInterest]

    for uid, poi_item in zip(ids, poi_list):
        if not poi_item:
            logging.debug('poi_item with id "%s" not found', uid)
            continue

        sections = []
        media_items = []
        for item in poi_item.media:
            if item.type not in (MediaType.IMAGE, MediaType.IMAGE_360, MediaType.VIDEO_YOUTUBE):
                continue
            media_items.append(BaseMediaTO(type=item.type,
                                           content=item.content,
                                           thumbnail_url=item.thumbnail_url))
        if media_items:
            sections.append(MediaSectionTO(ratio=SizeTO(width=16, height=9), items=media_items))

        vertical_list = ListSectionTO(style=ListSectionStyle.VERTICAL, items=[])

        params = {
            'q': poi_item.get_address_line(lang),
        }
        geo_url = 'geo://%s,%s?%s' % (
            poi_item.location.coordinates.lat, poi_item.location.coordinates.lon, urllib.urlencode(params, doseq=True))
        address_item = LinkListSectionItemTO(icon='fa-map-marker',
                                             title=params['q'],
                                             url=geo_url)
        vertical_list.items.append(address_item)

        if poi_item.description:
            description_item = ExpandableListSectionItemTO(icon='fa-info', title=poi_item.description)
            vertical_list.items.append(description_item)

        opening_hours_model = poi_item.opening_hours
        if opening_hours_model and opening_hours_model.type in (
            OpeningHours.TYPE_TEXTUAL, OpeningHours.TYPE_NOT_RELEVANT):
            if opening_hours_model.text:
                openinghours_item = ExpandableListSectionItemTO(icon='fa-clock-o',
                                                                title=opening_hours_model.text)
                vertical_list.items.append(openinghours_item)
        elif opening_hours_model and opening_hours_model.type == OpeningHours.TYPE_STRUCTURED:
            opening_hours_to = OpeningHoursTO.from_model(opening_hours_model)
            opening_hours_to.id = None
            openinghours_item = OpeningHoursSectionItemTO(
                icon='fa-clock-o',
                title=opening_hours_model.title,
                timezone=poi_item.location.timezone,
                opening_hours=opening_hours_to
            )
            vertical_list.items.append(openinghours_item)

        if vertical_list.items:
            sections.append(vertical_list)

        map_items.append(MapItemDetailsTO(id=uid,
                                          geometry=[],
                                          sections=sections))
    return map_items
