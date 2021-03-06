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

from __future__ import unicode_literals

import hashlib
import itertools
import json
import urllib

import logging
import time
from google.appengine.api import urlfetch
from google.appengine.ext import ndb, db
from google.appengine.ext.ndb.query import Cursor
from typing import List, Optional, Tuple

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.models import CommunityMapSettings
from rogerthat.bizz.elasticsearch import delete_index, create_index, es_request, delete_doc, index_doc, \
    execute_bulk_request
from rogerthat.bizz.maps.services.places import get_place_details, PlaceDetails, get_place_type_keys
from rogerthat.bizz.maps.shared import get_map_response
from rogerthat.bizz.opening_hours import get_opening_hours_info, OPENING_HOURS_GREEN_COLOR, OPENING_HOURS_RED_COLOR, \
    OPENING_HOURS_ORANGE_COLOR, get_opening_hours_lines, get_openinghours_color
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.profile import get_user_profile, get_service_profile
from rogerthat.dal.service import get_service_menu_items
from rogerthat.models import UserProfileInfo, OpeningHours, ServiceIdentity, \
    ServiceTranslation, ServiceRole, UserProfile, App, AppServiceFilter, ServiceProfile
from rogerthat.models.elasticsearch import ElasticsearchSettings
from rogerthat.models.maps import MapSavedItem, MapService, \
    MapServiceListItem, MapServiceMediaItem
from rogerthat.models.news import NewsItem
from rogerthat.models.settings import ServiceInfo, ServiceLocation
from rogerthat.rpc import users
from rogerthat.to import GeoPointTO
from rogerthat.to.maps import GetMapResponseTO, MapFunctionality, MapBaseUrlsTO, GetMapItemsResponseTO, \
    GetMapItemsRequestTO, GetMapItemDetailsResponseTO, GetMapItemDetailsRequestTO, ToggleMapItemResponseTO, \
    ToggleMapItemRequestTO, GetSavedMapItemsResponseTO, GetSavedMapItemsRequestTO, ToggleListSectionItemTO, \
    LinkListSectionItemTO, ListSectionTO, ListSectionStyle, MapItemDetailsTO, MapItemTO, MapIconTO, \
    MapListSectionItemType, ExpandableListSectionItemTO, \
    MediaSectionTO, SearchSuggestionTO, MapItemLineTextTO, \
    MapItemLineTextPartTO, GetMapSearchSuggestionsResponseTO, \
    GetMapSearchSuggestionsRequestTO, MapSearchSuggestionKeywordTO, \
    MapSearchSuggestionItemTO, OpeningHoursSectionItemTO, OpeningHoursTO, NewsGroupSectionTO, NewsSectionTO, \
    OpeningHoursListSectionItemTO, OpeningInfoTO
from rogerthat.to.news import GetNewsStreamFilterTO, SizeTO, BaseMediaTO
from rogerthat.translations import localize
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.service import add_slash_default, remove_slash_default, \
    get_service_identity_tuple, \
    create_service_identity_user

SERVICES_TAG = 'services'

ORGANIZATION_TYPE_SEARCH_PREFIX = 'organization-type-'


class SearchTag(object):

    @staticmethod
    def environment(demo):
        # type: (bool) -> unicode
        return 'environment#%s' % ('demo' if demo else 'production')

    @staticmethod
    def community(community_id):
        return 'community_id#%s' % community_id

    @staticmethod
    def country(country_code):
        azzert(country_code, 'Country code must not be empty')
        return 'country#%s' % country_code

    @staticmethod
    def vouchers(provider_id):
        return 'vouchers#%s' % provider_id

    @staticmethod
    def place_type(place_type):
        return 'place_type#%s' % place_type

    @staticmethod
    def organization_type(organization_type):
        # type: (int) -> unicode
        return 'organization_type#%d' % organization_type

    @staticmethod
    def visible_for_end_user():
        # type: () -> unicode
        return 'visible'

    @staticmethod
    def poi_status(status):
        # type: (int) -> unicode
        return 'poi_status#%d' % status


def get_clean_language_code(lang):
    if '_' in lang:
        return lang.split('_')[0]
    return lang


def get_tags_app(app):
    # type: (App) -> Tuple[List[unicode], List[int]]
    tags = [SearchTag.environment(app.demo)]
    community_ids = []
    if app.service_filter_type == AppServiceFilter.COUNTRY:
        tags.append(SearchTag.country(app.country))
    elif app.service_filter_type == AppServiceFilter.COMMUNITIES:
        community_ids = app.community_ids
    return tags, community_ids


@returns(GetMapResponseTO)
@arguments(app_user=users.User)
def get_map(app_user):
    user_profile = get_user_profile(app_user)
    language = user_profile.language
    community_id = user_profile.community_id
    models = ndb.get_multi([CommunityMapSettings.create_key(community_id),
                            UserProfileInfo.create_key(app_user)])
    map_config, user_profile_info = models  # type: CommunityMapSettings,  UserProfileInfo
    map_config = map_config or CommunityMapSettings.get_default(community_id)
    response = get_map_response(map_config, SERVICES_TAG, user_profile_info, [], add_addresses=False)
    response.functionalities = [MapFunctionality.CURRENT_LOCATION,
                                MapFunctionality.SEARCH,
                                MapFunctionality.SAVE]

    action_place_types = ['restaurant', 'bar', 'supermarket', 'bakery', 'butcher_shop', 'clothing_store', 'pharmacy',
                          'establishment_poi']
    response.action_chips = [
        get_organization_type_search_suggestion(ServiceProfile.ORGANIZATION_TYPE_PROFIT, language),
        get_organization_type_search_suggestion(ServiceProfile.ORGANIZATION_TYPE_EMERGENCY, language),
        get_organization_type_search_suggestion(ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT, language),
    ]
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


def get_organization_type_search_suggestion(organization_type, language):
    translation = localize(language, ServiceProfile.ORGANIZATION_TYPE_TRANSLATION_KEYS[organization_type])
    icon = ServiceProfile.ORGANIZATION_TYPE_ICONS[organization_type]
    return SearchSuggestionTO(icon=icon, title=translation)


@returns(GetMapSearchSuggestionsResponseTO)
@arguments(app_user=users.User, request=GetMapSearchSuggestionsRequestTO)
def get_map_search_suggestions(app_user, request):
    response = GetMapSearchSuggestionsResponseTO(items=[])

    user_profile = get_user_profile(app_user)
    lang = user_profile.language

    start_time = time.time()
    suggestions = _suggest_place_types(request.search.query, get_clean_language_code(lang))
    logging.warning(suggestions)
    took_time = time.time() - start_time
    logging.info('debugging.services._suggest_place_types _search {0:.3f}s'.format(took_time))
    for suggestion in suggestions:
        if suggestion.startswith(ORGANIZATION_TYPE_SEARCH_PREFIX):
            organization_type = int(suggestion.replace(ORGANIZATION_TYPE_SEARCH_PREFIX, ''))
            translation_key = ServiceProfile.ORGANIZATION_TYPE_TRANSLATION_KEYS[organization_type]
            response.items.append(MapSearchSuggestionKeywordTO(text=localize(lang, translation_key)))
            continue
        place_details = get_place_details(suggestion, lang)
        if not place_details:
            continue
        response.items.append(MapSearchSuggestionKeywordTO(text=place_details.title))

    app_id = get_app_id_from_app_user(app_user)
    app = get_app_by_id(app_id)
    tags, community_ids = get_tags_app(app)
    start_time = time.time()
    services = _suggest_services(tags,
                                 request.coords.lat,
                                 request.coords.lon,
                                 request.search.query,
                                 community_ids)
    took_time = time.time() - start_time
    logging.info('debugging.services._suggest_services _search {0:.3f}s'.format(took_time))
    for service in services:
        response.items.append(MapSearchSuggestionItemTO(id=remove_slash_default(users.User(service['email'])).email(),
                                                        text=service['name']))

    return response


@returns(GetMapItemsResponseTO)
@arguments(app_user=users.User, request=GetMapItemsRequestTO)
def get_map_items(app_user, request):
    center_lat = request.coords.lat
    center_lon = request.coords.lon
    distance = request.distance

    app_id = get_app_id_from_app_user(app_user)
    app = get_app_by_id(app_id)
    tags, community_ids = get_tags_app(app)

    search_tags = []
    if request.search:
        user_profile = get_user_profile(app_user)
        lang = user_profile.language
        start_time = time.time()
        place_type_or_org_type = _search_place_types_and_organization_types(request.search.query,
                                                                            get_clean_language_code(lang))
        took_time = time.time() - start_time
        if place_type_or_org_type:
            if place_type_or_org_type.startswith(ORGANIZATION_TYPE_SEARCH_PREFIX):
                organization_type = _get_organization_type_from_search_result(place_type_or_org_type)
                search_tags = [SearchTag.organization_type(organization_type)]
            else:
                search_tags = [SearchTag.place_type(place_type_or_org_type)]
        logging.info('debugging.services._search_place_types _search {0:.3f}s'.format(took_time))
        logging.debug('get_map_items.search: "%s" -> %s', request.search.query, search_tags)
    return _get_items(app_user, tags, search_tags, center_lat, center_lon, distance, cursor=request.cursor,
                      search=None if search_tags else request.search, community_ids=community_ids)


def _get_organization_type_from_search_result(result):
    organization_type = int(result.replace(ORGANIZATION_TYPE_SEARCH_PREFIX, ''))
    if organization_type not in ServiceProfile.ORGANIZATION_TYPE_TRANSLATION_KEYS:
        logging.error('Invalid organization type for search result: %s -> %s', result)
    return organization_type


@returns(GetMapItemDetailsResponseTO)
@arguments(app_user=users.User, request=GetMapItemDetailsRequestTO)
def get_map_item_details(app_user, request):
    return GetMapItemDetailsResponseTO(items=_get_map_item_details_to_from_ids(app_user, request.ids))


@returns(ToggleMapItemResponseTO)
@arguments(app_user=users.User, request=ToggleMapItemRequestTO)
def save_map_item(app_user, request):
    key = MapSavedItem.create_key(request.tag, app_user, request.item_id)
    saved = request.state == 'save'
    if saved:
        MapSavedItem(key=key, item_id=request.item_id).put()
    else:
        key.delete()

    user_profile = get_user_profile(app_user)
    lang = user_profile.language

    item = _get_saved_toggle_item(saved, color=None, language=lang)  # TODO: color
    return ToggleMapItemResponseTO(item_id=request.item_id, toggle_item=item)


@returns(GetSavedMapItemsResponseTO)
@arguments(app_user=users.User, request=GetSavedMapItemsRequestTO)
def get_saved_map_items(app_user, request):
    cursor = request.cursor or None
    batch_count = 50 if cursor else 10
    qry = MapSavedItem.list_by_date(request.tag, app_user)

    r = GetSavedMapItemsResponseTO()
    items, new_cursor, has_more = qry.fetch_page(
        batch_count, start_cursor=Cursor.from_websafe_string(cursor) if cursor else None, keys_only=True)

    ids = [item.id() for item in items]
    r.items = _get_map_item_to_from_ids(app_user, ids)
    if has_more:
        r.cursor = new_cursor.to_websafe_string().decode('utf-8') if new_cursor else None
    else:
        r.cursor = None
    return r


def get_service_uid(service_identity_user):
    return hashlib.sha256((service_identity_user.email()).encode('utf8')).hexdigest()


def cleanup_map_index(service_identity_user):
    uid = get_service_uid(service_identity_user)
    return delete_doc(_get_elasticsearch_index(), uid)


def add_map_index(service_identity_user, locations, name, tags, txt):
    from rogerthat.to.activity import GEO_POINT_FACTOR
    uid = get_service_uid(service_identity_user)
    doc = {
        'email': service_identity_user.email(),
        'name': name,
        'suggestion': name,
        'location': [],
        'tags': tags,
        'txt': txt
    }
    for loc in locations:
        lat = float(loc.lat) / GEO_POINT_FACTOR
        lon = float(loc.lon) / GEO_POINT_FACTOR
        doc['location'].append({'lat': lat, 'lon': lon})

    return index_doc(_get_elasticsearch_index(), uid, doc)


def _get_saved_toggle_item(saved, color, language):
    return ToggleListSectionItemTO(type=MapListSectionItemType.TOGGLE,
                                   id=ToggleListSectionItemTO.TOGGLE_ID_SAVE,
                                   state='saved' if saved else 'save',
                                   filled=saved,
                                   icon='fa-heart' if saved else 'fa-heart-o',
                                   icon_color=color,
                                   title=localize(language, 'saved' if saved else 'save'))


def _get_all_translations(service_profile):
    from rogerthat.bizz.i18n import get_all_translations, get_active_translation_set
    s = get_active_translation_set(service_profile)
    if s:
        translation_types = ServiceTranslation.HOME_TYPES + ServiceTranslation.IDENTITY_TYPES
        translations = get_all_translations(s, translation_types)
        return translations


# TODO lucas: use convert_section_template_to_item for this, and define the template here somewhere.
def save_map_service(service_identity_user):
    from rogerthat.bizz.i18n import DummyTranslator, Translator

    service_user, service_identity = get_service_identity_tuple(service_identity_user)
    map_service_key = MapService.create_key(service_identity_user.email())

    keys = [ServiceInfo.create_key(service_user, service_identity),
            OpeningHours.create_key(service_user, service_identity)]
    service_info, opening_hours = ndb.get_multi(keys)  # type: ServiceInfo, OpeningHours
    if not service_info:
        map_service_key.delete()
        return None

    if service_identity == ServiceIdentity.DEFAULT:
        email = service_user.email()
    else:
        email = service_identity_user.email()

    service_profile = get_service_profile(service_user)
    lang = service_profile.defaultLanguage
    translations = _get_all_translations(service_profile)
    if translations:
        translator = Translator(translations, service_profile.supportedLanguages)
    else:
        translator = DummyTranslator(lang)

    map_service = MapService(key=map_service_key)
    map_service.title = service_info.name
    map_service.main_place_type = service_info.main_place_type
    map_service.place_types = service_info.place_types
    map_service.has_news = NewsItem.list_by_sender(service_identity_user).count(1) > 0
    map_service.media_items = [MapServiceMediaItem(item=BaseMediaTO(type=item.type,
                                                                    content=item.content,
                                                                    thumbnail_url=item.thumbnail_url))
                               for item in service_info.media]

    if opening_hours and opening_hours.type in (OpeningHours.TYPE_TEXTUAL, OpeningHours.TYPE_NOT_RELEVANT):
        if opening_hours.text and opening_hours.text.strip():
            map_service.vertical_items.append(MapServiceListItem(
                item=ExpandableListSectionItemTO(icon='fa-clock-o',
                                                 title=opening_hours.text)
            ))
    elif opening_hours and opening_hours.type == OpeningHours.TYPE_STRUCTURED:
        map_service.opening_hours_links.append(opening_hours.key)
        map_service.vertical_items.append(MapServiceListItem(
            item=OpeningHoursSectionItemTO(
                icon='fa-clock-o',
                title=opening_hours.title,
                timezone=service_info.timezone,
                opening_hours=OpeningHoursTO.from_model(opening_hours)
            )
        ))
        # TODO: Backwards compat - remove when most apps support OpeningHoursSectionTO
        map_service.vertical_items.append(MapServiceListItem(
            item=OpeningHoursListSectionItemTO(
                icon='fa-clock-o',
                title=opening_hours.title,
            )
        ))

    if service_info.description:
        description_item = ExpandableListSectionItemTO(icon='fa-info', title=service_info.description)
        map_service.vertical_items.append(MapServiceListItem(item=description_item))

    for i, phone_number in enumerate(service_info.phone_numbers):
        v_phone_item = LinkListSectionItemTO(icon='fa-phone',
                                             title=phone_number.name or phone_number.value,
                                             url='tel://%s' % phone_number.value)

        map_service.vertical_items.append(MapServiceListItem(item=v_phone_item))
        if i == 0:
            horizontal_item = MapServiceListItem(item=LinkListSectionItemTO(icon=v_phone_item.icon,
                                                                            title=localize(lang, 'Call'),
                                                                            url=v_phone_item.url))
            map_service.horizontal_items.append(horizontal_item)

    for i, address in enumerate(service_info.addresses):  # type: int, ServiceLocation
        params = {
            'q': address.get_address_line(lang),
        }
        geo_url = 'geo://%s,%s?%s' % (
            address.coordinates.lat, address.coordinates.lon, urllib.urlencode(params, doseq=True))
        if i == 0:
            map_service.address = '%s %s, %s' % (address.street, address.street_number, address.locality)
            map_service.geo_location = address.coordinates
            h_map_item = LinkListSectionItemTO(icon='fa-location-arrow',
                                               title=localize(lang, 'Directions'),
                                               url=geo_url)
            map_service.horizontal_items.append(MapServiceListItem(item=h_map_item))

        v_map_item = LinkListSectionItemTO(icon='fa-map-marker',
                                           title=map_service.address,
                                           url=geo_url)
        map_service.vertical_items.append(MapServiceListItem(item=v_map_item))

    for smd in get_service_menu_items(service_identity_user):
        if smd.tag in ('when_where',):
            continue
        url_dict = {
            'action_type': 'click',
            'action': smd.hashed_tag,
            'title': translator.translate(ServiceTranslation.HOME_TEXT, smd.label, lang),
            'service': email
        }
        icon = smd.iconName if smd.iconName and smd.iconName.startswith('fa-') else None
        item = MapServiceListItem(role_ids=['%s' % role for role in smd.roles],
                                  item=LinkListSectionItemTO(icon=icon or 'fa-rocket',
                                                             icon_color=smd.iconColor,
                                                             title=url_dict['title'],
                                                             url='open://%s' % json.dumps(url_dict)))
        map_service.vertical_items.append(item)

    map_service.put()
    return map_service


def _user_has_role(service_identity_user, user_profile, role):
    # type: (users.User, UserProfile, str) -> bool
    service_user, identity = get_service_identity_tuple(service_identity_user)
    if user_profile.has_role(service_identity_user, role):
        return True
    if identity == ServiceIdentity.DEFAULT:
        return False
    return user_profile.has_role(create_service_identity_user(service_user), role)


def _item_is_visible(service_identity_user, user_profile, role_ids, existing_role_ids):
    # type: (users.User, UserProfile, List[str], List[int]) -> bool
    if not role_ids:
        return True
    for role_id in role_ids:
        if long(role_id) in existing_role_ids and _user_has_role(service_identity_user, user_profile, role_id):
            return True
    return False


def _get_map_item_details_to_from_ids(app_user, ids):
    from rogerthat.bizz.news import get_items_for_filter
    user_profile = get_user_profile(app_user)
    lang = user_profile.language
    map_items = []
    service_identity_users = [add_slash_default(users.User(email)) for email in ids]
    map_services = ndb.get_multi([MapService.create_key(user.email())
                                  for user in service_identity_users])  # type: List[MapService]

    models_to_get = []
    all_service_role_keys = set()
    for id_, map_service in zip(ids, map_services):
        service_user, service_identity = get_service_identity_tuple(users.User(map_service.service_identity_email))
        models_to_get.append(MapSavedItem.create_key(SERVICES_TAG, app_user, id_))
        for item in map_service.vertical_items:
            if isinstance(item.item, OpeningHoursListSectionItemTO):
                models_to_get.extend(map_service.opening_hours_links)
                models_to_get.append(ServiceInfo.create_key(service_user, service_identity))
            all_service_role_keys.update({ServiceRole.create_key(service_user, long(role_id)) for role_id in item.role_ids})
        for item in map_service.horizontal_items:
            all_service_role_keys.update({ServiceRole.create_key(service_user, long(role_id)) for role_id in item.role_ids})
        for item in map_service.media_items:
            all_service_role_keys.update({ServiceRole.create_key(service_user, long(role_id)) for role_id in item.role_ids})
    models = ndb.get_multi(models_to_get)
    all_opening_hours = {model.key: model for model in models if isinstance(model, OpeningHours)}
    service_infos = {model.key: model for model in models if isinstance(model, ServiceInfo)}
    all_saved_items = {model.id for model in models if isinstance(model, MapSavedItem)}
    role_ids = {role.role_id for role in db.get(list(all_service_role_keys)) if role} if all_service_role_keys else []

    for id_, service_identity_user, map_service in zip(ids, service_identity_users, map_services):
        service_user, service_identity = get_service_identity_tuple(users.User(map_service.service_identity_email))
        if not map_service:
            logging.debug('map_service with id "%s" not found', service_identity_user.email())
            continue

        sections = []

        media_items = [item.item for item in map_service.media_items
                       if _item_is_visible(service_identity_user, user_profile, item.role_ids, role_ids)]
        if media_items:
            sections.append(MediaSectionTO(ratio=SizeTO(width=16, height=9), items=media_items))

        horizontal_list_items = [item.item for item in map_service.horizontal_items
                                 if _item_is_visible(service_identity_user, user_profile, item.role_ids,
                                                     role_ids)]
        is_saved = id_ in all_saved_items
        save_item = _get_saved_toggle_item(is_saved, None, lang)
        horizontal_list_items.append(save_item)
        sections.append(ListSectionTO(style=ListSectionStyle.HORIZONTAL, items=horizontal_list_items))

        vertical_list_items = []

        for item in map_service.vertical_items:
            if not _item_is_visible(service_identity_user, user_profile, item.role_ids, role_ids):
                continue

            # TODO: remove this after most apps support OpeningHoursSectionItemTO
            if isinstance(item.item, OpeningHoursListSectionItemTO):
                for opening_hours_key in map_service.opening_hours_links:
                    opening_hours = all_opening_hours.get(opening_hours_key)  # type: OpeningHours
                    if not opening_hours:
                        continue
                    service_info = service_infos.get(ServiceInfo.create_key(service_user, service_identity))
                    if not service_info:
                        continue
                    now_open, open_until, extra_description, weekday_text = get_opening_hours_info(
                        opening_hours, service_info.timezone, lang)
                    item.item.opening_hours = OpeningInfoTO(name=opening_hours.title,
                                                            title=localize(lang, 'open' if now_open else 'closed'),
                                                            title_color=get_openinghours_color(
                                                                OPENING_HOURS_GREEN_COLOR if now_open else OPENING_HOURS_RED_COLOR),
                                                            subtitle=open_until,
                                                            description=extra_description,
                                                            description_color=get_openinghours_color(
                                                                OPENING_HOURS_ORANGE_COLOR),
                                                            weekday_text=weekday_text)
                    vertical_list_items.append(item.item)
            else:
                vertical_list_items.append(item.item)

        if vertical_list_items:
            sections.append(ListSectionTO(style=ListSectionStyle.VERTICAL,
                                          items=vertical_list_items))

        if map_service.has_news:
            community_id = get_service_profile(service_user).community_id
            stream_filter = GetNewsStreamFilterTO(service_identity_email=service_identity_user.email())
            result = get_items_for_filter(stream_filter, community_id=community_id, amount=3)
            news_section = NewsGroupSectionTO()
            news_section.filter = stream_filter
            news_section.group_id = result.group_id
            news_section.items = result.items
            news_section.placeholder_image = 'https://storage.googleapis.com/oca-files/map/news/billboard_placeholder.png'
            sections.append(news_section)
            # TODO: remove after most clients support NewsGroupSectionTO
            # Then also remove NewsSectionTO model
            sections.append(NewsSectionTO(filter=stream_filter,
                                          limit=3,
                                          placeholder_image='https://storage.googleapis.com/oca-files/map/news/billboard_placeholder.png'))
        map_items.append(MapItemDetailsTO(id=id_,
                                          geometry=[],
                                          sections=sections))
    return map_items


def _get_map_item_to_from_ids(app_user, ids):
    items = []
    up = get_user_profile(app_user)
    map_services = ndb.get_multi([MapService.create_key(add_slash_default(users.User(id_)).email())
                                  for id_ in ids])  # type: List[MapService]
    models_to_get = []
    for map_service in map_services:
        if not map_service:
            continue
        models_to_get.extend(map_service.opening_hours_links)
        service_user, service_identity = get_service_identity_tuple(users.User(map_service.service_identity_email))
        models_to_get.append(ServiceInfo.create_key(service_user, service_identity))

    models = ndb.get_multi(models_to_get)
    all_opening_hours = {model.key: model for model in models if isinstance(model, OpeningHours)}
    service_infos = {model.key: model for model in models if isinstance(model, ServiceInfo)}
    for map_service in map_services:
        if not map_service:
            logging.debug('map_service with id "%s" not found', map_service.service_identity_email)
            continue
        opening_hours = [all_opening_hours[key] for key in map_service.opening_hours_links if key in all_opening_hours]
        service_user, service_identity = get_service_identity_tuple(users.User(map_service.service_identity_email))
        service_info = service_infos.get(ServiceInfo.create_key(service_user, service_identity))
        if not service_info:
            logging.debug('service_info with id "%s" not found', map_service.service_identity_email)
            continue
        items.append(_convert_to_item_to(map_service, up.language, service_info.timezone, opening_hours))
    return items


def _convert_to_item_to(map_service, language, timezone, opening_hours):
    # type: (MapService, str, str, List[OpeningHours]) -> MapItemTO

    lines = []
    line_1 = []
    for place_type in map_service.place_types:
        place_details = get_place_details(place_type, language)
        if not place_details:
            continue
        line_1.append(place_details.title)
    main_place_details = get_place_details(map_service.main_place_type, language)
    if main_place_details:
        icon_id = main_place_details.png_icon
        icon_color = main_place_details.icon_color
    else:
        icon_id = PlaceDetails.png_icon.default
        icon_color = PlaceDetails.icon_color.default

    if line_1:
        lines.append(MapItemLineTextTO(parts=[MapItemLineTextPartTO(color=None, text=txt) for txt in line_1]))

    if map_service.address:
        lines.append(MapItemLineTextTO(parts=[MapItemLineTextPartTO(color=None, text=', '.join(map_service.address.splitlines()))]))

    if opening_hours:
        opening_hours_model = opening_hours[0]
        if opening_hours_model.type == OpeningHours.TYPE_STRUCTURED:
            lines.extend(get_opening_hours_lines(opening_hours_model, language, timezone))

    return MapItemTO(id=remove_slash_default(users.User(map_service.service_identity_email)).email(),
                     coords=GeoPointTO(lat=map_service.geo_location.lat,
                                       lon=map_service.geo_location.lon),
                     icon=MapIconTO(id=icon_id,
                                    color=icon_color),
                     title=map_service.title,
                     description=None,
                     lines=lines)


def _get_items(app_user, tags, place_type_tags, lat, lon, distance, limit=100, cursor=None, search=None,
               community_ids=None):
    if limit > 1000:
        limit = 1000
    start_time = time.time()
    new_cursor, result_ids = _search_services(tags, place_type_tags, lat, lon, distance, cursor, limit, search,
                                              community_ids)
    took_time = time.time() - start_time
    logging.info('debugging.services._get_items _search {0:.3f}s'.format(took_time))
    items = []
    up = get_user_profile(app_user)
    map_services = [m for m in ndb.get_multi([MapService.create_key(id_)
                                              for id_ in result_ids]) if m]  # type: List[MapService]
    models_to_get = []
    for map_service in map_services:
        models_to_get.extend(map_service.opening_hours_links)
        service_user, service_identity = get_service_identity_tuple(users.User(map_service.service_identity_email))
        models_to_get.append(ServiceInfo.create_key(service_user, service_identity))

    models = ndb.get_multi(models_to_get)
    all_opening_hours = {model.key: model for model in models if isinstance(model, OpeningHours)}
    service_infos = {model.key: model for model in models if isinstance(model, ServiceInfo)}

    for map_service in map_services:
        opening_hours = [all_opening_hours[key] for key in map_service.opening_hours_links]
        service_user, service_identity = get_service_identity_tuple(users.User(map_service.service_identity_email))
        service_info = service_infos.get(ServiceInfo.create_key(service_user, service_identity))
        if not service_info:
            logging.debug('service_info with id "%s" not found', map_service.service_identity_email)
            continue
        items.append(_convert_to_item_to(map_service, up.language, service_info.timezone, opening_hours))

    return GetMapItemsResponseTO(cursor=new_cursor,
                                 items=items,
                                 distance=distance,
                                 top_sections=[])


def _get_elasticsearch_index():
    return ElasticsearchSettings.create_key().get().services_index


def _delete_index():
    return delete_index(_get_elasticsearch_index())


def _create_index():
    request = {
        'mappings': {
            'properties': {
                'email': {
                    'type': 'keyword'
                },
                'name': {
                    'type': 'keyword'
                },
                'suggestion': {
                    'type': 'search_as_you_type'
                },
                'location': {
                    'type': 'geo_point'
                },
                'tags': {
                    'type': 'keyword'
                },
                'txt': {
                    'type': 'text'
                },
            }
        }
    }
    return create_index(_get_elasticsearch_index(), request)


def _suggest_services(tags, lat, lon, search, community_ids):
    # type: (List[unicode], float, float, str, List[int]) -> List[dict]
    qry = {
        'size': 12,
        'from': 0,
        '_source': {
            'includes': [],
        },
        'query': {
            'bool': {
                'must': [
                    {
                        'multi_match': {
                            # See https://www.elastic.co/guide/en/elasticsearch/reference/7.x/search-as-you-type.html
                            'query': search,
                            'fields': ['suggestion',
                                       'suggestion._2gram',
                                       'suggestion._3gram'],
                            'type': 'bool_prefix'
                        }
                    }
                ],
                'filter': [{'term': {'tags': tag}} for tag in tags],
            }
        },
        'sort': [
            {'_score': {'order': 'desc'}},
            {
                '_geo_distance': {
                    'location': {
                        'lat': lat,
                        'lon': lon
                    },
                    'order': 'asc',
                    'unit': 'm'
                }
            }
        ]
    }

    if community_ids:
        # Must match one of the specified community ids
        qry['query']['bool']['must'].append({
            'bool': {
                'should': [{'term': {'tags': SearchTag.community(community_id)}} for community_id in community_ids],
                'minimum_should_match': 1
            }
        })

    path = '/%s/_search' % _get_elasticsearch_index()
    result_data = es_request(path, urlfetch.POST, qry)
    results = []
    for hit in result_data['hits']['hits']:
        results.append({'email': hit['_source']['email'], 'name': hit['_source']['name']})
    return results


def search_services_by_tags(tags, cursor, limit, query):
    # type: (List[str], Optional[str], int, Optional[str]) -> Tuple[List[users.User], Optional[str]]
    # Search services filtered only by tags, sorted by name
    start_offset = long(cursor) if cursor else 0
    if (start_offset + limit) > 10000:
        limit = 10000 - start_offset
    if limit <= 0:
        return [], None
    qry = {
        'size': limit,
        'from': start_offset,
        '_source': {
            'includes': ['email'],
        },
        'query': {
            'bool': {
                'filter': [{'term': {'tags': tag}} for tag in tags],
                'must': [],
                'should': [],
            }
        },
        'sort': [
            {'name': {'order': 'asc'}},
        ]
    }
    if query:
        qry['query']['bool']['must'].append({
            'multi_match': {
                'query': query,
                'fields': ['suggestion'],
                'fuzziness': 'auto',
            }
        })
        qry['sort'].insert(0, {'_score': {'order': 'desc'}})

    path = '/%s/_search' % _get_elasticsearch_index()
    result_data = es_request(path, urlfetch.POST, qry)
    new_cursor = None
    next_offset = start_offset + len(result_data['hits']['hits'])
    if result_data['hits']['total']['relation'] in ('eq', 'gte'):
        if result_data['hits']['total']['value'] > next_offset and next_offset < 10000:
            new_cursor = '%s' % next_offset
    results = [users.User(hit['_source']['email']) for hit in result_data['hits']['hits']]
    return results, new_cursor


def _search_services(tags, place_type_tags, lat, lon, distance, cursor, limit, search=None, community_ids=None):
    # we can only fetch up to 10000 items with from param
    start_offset = long(cursor) if cursor else 0

    if (start_offset + limit) > 10000:
        limit = 10000 - start_offset
    if limit <= 0:
        return None, []

    qry = {
        'size': limit,
        'from': start_offset,
        '_source': {
            'includes': ['email', 'name'],
            # 'excludes': []
        },
        'query': {
            'bool': {
                'must': [],
                'filter': [],
                'should': []
            }
        },
        'sort': [
            {
                '_geo_distance': {
                    'location': {
                        'lat': lat,
                        'lon': lon
                    },
                    'order': 'asc',
                    'unit': 'm'
                }
            },
            "_score",
        ]
    }

    # Must match all tags
    for tag in tags:
        qry['query']['bool']['filter'].append({
            'term': {
                'tags': tag
            }
        })

    if place_type_tags:
        # Must match one of the specified place types
        qry['query']['bool']['must'].append({
            'bool': {
                'should': [{'term': {'tags': tag}} for tag in place_type_tags],
                "minimum_should_match": 1
            }
        })

        if search:
            qry['query']['bool']['should'].append({
                'multi_match': {
                    'query': search.query,
                    'fields': ['name^500', 'txt^5'],
                    "fuzziness": "1"
                }
            })
    if community_ids:
        # Must match one of the specified community ids
        qry['query']['bool']['must'].append({
            'bool': {
                'should': [{'term': {'tags': SearchTag.community(community_id)}} for community_id in community_ids],
                'minimum_should_match': 1
            }
        })

    elif search:
        qry['query']['bool']['must'].append({
            'multi_match': {
                'query': search.query,
                'fields': ['name^500', 'txt^5'],
                "operator": "and"
            }
        })
    else:
        qry['query']['bool']['filter'].append({
            'geo_distance': {
                'distance': '%sm' % distance,
                'location': {
                    'lat': lat,
                    'lon': lon
                }
            }
        })

    path = '/%s/_search' % _get_elasticsearch_index()
    result_data = es_request(path, urlfetch.POST, qry)

    new_cursor = None
    if place_type_tags or search:
        pass # no cursor
    else:
        next_offset = start_offset + len(result_data['hits']['hits'])
        if result_data['hits']['total']['relation'] in ('eq', 'gte'):
            if result_data['hits']['total']['value'] > next_offset and next_offset < 10000:
                new_cursor = '%s' % next_offset

    result_ids = []
    for hit in result_data['hits']['hits']:
        result_ids.append(hit['_source']['email'])
    return new_cursor, result_ids


def _get_elasticsearch_place_type_index():
    return ElasticsearchSettings.create_key().get().place_types_index


def _delete_place_type_index():
    return delete_index(_get_elasticsearch_place_type_index())


def _create_place_type_index():
    request = {
        'mappings': {
            'properties': {
                'title_en': {
                    'type': 'text',
                    'analyzer': 'english'
                },
                'suggestion_en': {
                    'type': 'search_as_you_type'
                },
                'title_nl': {
                    'type': 'text',
                    'analyzer': 'dutch'
                },
                'suggestion_nl': {
                    'type': 'search_as_you_type'
                },
            }
        }
    }
    return create_index(_get_elasticsearch_place_type_index(), request)


def _index_place_type(place_type):
    place_details_en = get_place_details(place_type, 'en')
    if not place_details_en:
        logging.error('Failed to index en place type %s', place_type)
        return []
    en_translations_suggest = [place_details_en.title]
    en_translations_search = [place_details_en.title]

    place_details_nl = get_place_details(place_type, 'nl')
    if not place_details_nl:
        logging.error('Failed to index nl place type %s', place_type)
        return []
    nl_translations_suggest = [place_details_nl.title]
    nl_translations_search = [place_details_nl.title]

    doc = {
        'title_en': list(en_translations_search),
        'suggestion_en': list(en_translations_suggest),
        'title_nl': list(nl_translations_search),
        'suggestion_nl': list(nl_translations_suggest),
    }
    return _index_doc_place_type(place_type, doc)


def _index_doc_place_type(place_type, doc):
    yield {'index': {'_id': place_type}}
    yield doc


def _index_organization_types():
    operations = []
    for organization_type, translation_key in ServiceProfile.ORGANIZATION_TYPE_TRANSLATION_KEYS.iteritems():
        if organization_type == ServiceProfile.ORGANIZATION_TYPE_UNSPECIFIED:
            continue
        operations.append({'index': {'_id': ORGANIZATION_TYPE_SEARCH_PREFIX + str(organization_type)}})
        doc = {}
        for language in ['en', 'nl']:
            translation = localize(language, translation_key)
            doc['title_' + language] = [translation]
            doc['suggestion_' + language] = [translation]
        operations.append(doc)
    return execute_bulk_request(_get_elasticsearch_place_type_index(), operations)


def _re_index_place_type(place_type):
    return execute_bulk_request(_get_elasticsearch_place_type_index(), _index_place_type(place_type))


def _re_index_place_types():
    operations = itertools.chain.from_iterable([_index_place_type(place_type) for place_type in get_place_type_keys()])
    return execute_bulk_request(_get_elasticsearch_place_type_index(), operations)


def index_search_keywords():
    _index_organization_types()
    _re_index_place_types()


def _search_place_types_and_organization_types(search_query, lang):
    # type: (str, str) -> Optional[str]
    qry = {
        'size': 3,
        'from': 0,
        '_source': {
            'includes': [],
        },
        'query': {
            'bool': {
                'must': [
                    {
                        'multi_match': {
                            'query': search_query,
                            'fields': ['title*',
                                       'title_%s^2' % lang],
                            'type': 'most_fields',
                            'fuzziness': '1'
                        }
                    }
                ]
            }
        },
        'sort': [
            {
                '_score': {
                    'order': 'desc'
                }
            }
        ]
    }

    path = '/%s/_search' % _get_elasticsearch_place_type_index()
    result_data = es_request(path, urlfetch.POST, qry)

    if result_data['hits']['hits']:
        search_query_lowercase = search_query.lower()
        hit = result_data['hits']['hits'][0]
        for title in hit['_source']['title_en']:
            if title.lower() == search_query_lowercase:
                return hit['_id']
        for title in hit['_source']['title_nl']:
            if title.lower() == search_query_lowercase:
                return hit['_id']
    return None


def _suggest_place_types(qry, lang):
    # type: (str, str) -> List[str]
    qry = {
        'size': 3,
        'from': 0,
        '_source': {
            'includes': [],
        },
        'query': {
            'multi_match': {
                'query': qry,
                'fields': ['suggestion*',
                           'suggestion*.2gram',
                           'suggestion*.3gram',
                           'suggestion_%s^2' % lang,
                           'suggestion_%s.2gram^2' % lang,
                           'suggestion_%s.3gram^2' % lang],
                'type': 'bool_prefix'
            }
        }
    }

    path = '/%s/_search' % _get_elasticsearch_place_type_index()
    result_data = es_request(path, urlfetch.POST, qry)
    return [hit['_id'] for hit in result_data['hits']['hits']]
