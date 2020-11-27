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
from __future__ import unicode_literals

import json
import logging
import urllib
from copy import deepcopy
from datetime import datetime

from dateutil.relativedelta import relativedelta
from google.appengine.api.app_identity.app_identity import get_application_id
from google.appengine.ext import db, ndb
from typing import Optional, Dict
from urllib3.contrib.appengine import AppEngineManager

import oca
from mcfw.exceptions import HttpBadRequestException
from mcfw.rpc import parse_complex_value
from oca import HomeScreenBottomNavigation, HomeScreenBottomSheet, \
    HomeScreenBottomSheetHeader, HomeScreen, HomeScreenContent, HomeScreenNavigationButton
from rogerthat.bizz.communities.communities import get_community
from rogerthat.consts import DEBUG
from rogerthat.dal.profile import get_service_profile, get_user_profile
from rogerthat.models import ServiceIdentity, OpeningHours, ServiceMenuDef
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.to.maps import TextSectionTO, ListSectionTO, OpeningHoursSectionItemTO, OpeningHoursTO, \
    ExpandableListSectionItemTO, LinkListSectionItemTO, MAP_SECTION_TYPES, ListSectionStyle, VerticalLinkListItemStyle, \
    HorizontalLinkListItemStyle, NewsGroupSectionTO
from rogerthat.translations import DEFAULT_LANGUAGE, localize
from solutions.common.models import SolutionBrandingSettings
from .models import CommunityHomeScreen, HomeScreenTestUser
from .to import BottomSheetSectionTemplate, TextSectionTemplate, BottomSheetSectionTemplateInstance, \
    ListSectionTemplate, NewsSectionTemplate, ExpandableItemTemplate, LinkItemTemplate, OpeningHoursItemTemplate, \
    ExpandableItemSource, LinkItemContentDefault, LinkItemSyncedContent, LinkItemSource, LinkItemAddress, \
    LinkItemServiceMenuItem
from ...news import get_items_for_filter
from ...profile import update_mobiles

TEST_HOME_SCREEN_ID = '_test_'

configuration = oca.Configuration(
    host='http://localhost:8333/api' if DEBUG else 'https://oca-dot-%s.ew.r.appspot.com/api' % get_application_id(),
    api_key={'X-OCA3-Api-Key': get_server_settings().oca3ApiKey},
)

oca_client = oca.ApiClient(configuration)
oca_client.rest_client.pool_manager = AppEngineManager()


def convert_section_template_to_item(row, service_info, opening_hours, language, community_id):
    # type: (BottomSheetSectionTemplate, ServiceInfo, OpeningHours, unicode, int) ->  Optional[MAP_SECTION_TYPES]
    menu_items_to_get = set()
    if isinstance(row, ListSectionTemplate):
        for item in row.items:
            if isinstance(item, LinkItemTemplate):
                if isinstance(item.content, LinkItemServiceMenuItem):
                    menu_items_to_get.add(item.content.service)
    menu_items_map = {}  # type: Dict[str, Dict[str, ServiceMenuDef]]
    for service_email in menu_items_to_get:
        menu_items_qry = ServiceMenuDef.list_by_service(users.User(service_email))
        menu_items_map[service_email] = {item.tag: item for item in menu_items_qry}

    if isinstance(row, TextSectionTemplate):
        text_section = TextSectionTO()
        text_section.title = row.title
        text_section.description = row.description
        return text_section
    elif isinstance(row, ListSectionTemplate):
        list_section = ListSectionTO()
        list_section.style = row.style
        items = []
        for item in row.items:
            if isinstance(item, OpeningHoursItemTemplate):
                items.append(OpeningHoursSectionItemTO(
                    icon='fa-clock-o',
                    title=opening_hours.title,
                    timezone=service_info.timezone,
                    opening_hours=OpeningHoursTO.from_model(opening_hours),
                ))
            elif isinstance(item, ExpandableItemTemplate):
                if item.source == ExpandableItemSource.NONE:
                    title = item.title
                elif item.source == ExpandableItemSource.SERVICE_INFO_DESCRIPTION:
                    item.icon = 'fa-info'
                    title = service_info.description
                else:
                    raise NotImplementedError('Unknown source on ExpandableItemTemplate: %s' % item.source)
                items.append(ExpandableListSectionItemTO(title=title, icon=item.icon))
            elif isinstance(item, LinkItemTemplate):
                link_item = LinkListSectionItemTO()
                link_item.icon_color = item.icon_color
                link_item.style = item.style
                content = item.content
                if isinstance(content, LinkItemContentDefault):
                    link_item.external = content.external
                    link_item.request_user_link = content.request_user_link
                    link_item.url = content.url
                    link_item.title = item.title
                    link_item.icon = item.icon or 'fa-globe'
                elif isinstance(content, LinkItemSyncedContent):
                    link_item.external = False
                    link_item.request_user_link = False
                    try:
                        if content.source == LinkItemSource.SERVICE_INFO_EMAIL:
                            email = service_info.email_addresses[content.index]
                            link_item.title = item.title or email.value
                            link_item.url = 'mailto://' + email.value
                            link_item.icon = item.icon or 'fa-envelope'
                        elif content.source == LinkItemSource.SERVICE_INFO_PHONE:
                            phone = service_info.phone_numbers[content.index]
                            link_item.title = item.title or phone.name or phone.value
                            link_item.url = 'tel://' + phone.value
                            link_item.icon = item.icon or 'fa-phone'
                        elif content.source == LinkItemSource.SERVICE_INFO_WEBSITE:
                            website = service_info.websites[content.index]
                            link_item.title = item.title or website.name or website.value
                            link_item.url = website.value
                            link_item.icon = item.icon or 'fa-globe'
                    except IndexError:
                        logging.debug('Skipping item %s: No data at index in service info %d', item,
                                      content.index)
                elif isinstance(content, LinkItemAddress):
                    link_item.external = False
                    link_item.request_user_link = False
                    if not service_info.addresses:
                        logging.debug('Skipping item %s: No address set', item)
                        continue
                    address = service_info.addresses[0]
                    params = {'q': address.get_address_line(language)}
                    geo_url = 'geo://%s,%s?%s' % (address.coordinates.lat, address.coordinates.lon,
                                                  urllib.urlencode(params, doseq=True))
                    address_line = '%s %s, %s' % (address.street, address.street_number, address.locality)
                    link_item.title = item.title or address_line
                    link_item.url = geo_url
                    link_item.icon = item.icon or 'fa-map-marker'
                elif isinstance(content, LinkItemServiceMenuItem):
                    menu_item = menu_items_map[content.service].get(content.tag)
                    if not menu_item:
                        raise HttpBadRequestException('No menu item found with tag %s for service %s!' % (
                            content.tag, content.service))
                    link_item.url = 'open://' + json.dumps({'action_type': 'click',
                                                            'action': ServiceMenuDef.hash_tag(content.tag),
                                                            'service': content.service})
                    link_item.title = item.title or menu_item.label
                    if not item.icon and menu_item.iconName and menu_item.iconName.startswith('fa'):
                        link_item.icon = menu_item.iconName
                    else:
                        link_item.icon = item.icon or 'fa-globe'
                else:
                    raise NotImplementedError('Unimplemented LinkItemTemplate.content: %s' % content)
                if not link_item.url:
                    raise Exception('Link item does not have an url: %s' % link_item)
                items.append(link_item)
        list_section.items = items
        return list_section
    elif isinstance(row, NewsSectionTemplate):
        result = get_items_for_filter(row.filter, community_id=community_id, amount=row.limit)
        if not result:
            return None
        news_section = NewsGroupSectionTO()
        news_section.filter = row.filter
        news_section.group_id = result.group_id
        news_section.items = result.items
        news_section.placeholder_image = 'https://storage.googleapis.com/oca-files/map/news/billboard_placeholder.png'
        return news_section
    else:
        raise NotImplementedError(row)


def maybe_publish_home_screens(service_user):
    # type: (users.User) -> None
    service_profile = get_service_profile(service_user)
    community_id = service_profile.community_id
    community = get_community(community_id)
    if community.main_service == service_user.email():
        for home_screen in CommunityHomeScreen.list_by_community(community_id):
            publish_home_screen(community_id, home_screen.id)


def publish_home_screen(community_id, home_screen_id, is_test=False, extra_sections=[]):
    # type: (int, unicode, bool, List[MAP_SECTION_TYPES]) -> None
    publish_home_screen_id = TEST_HOME_SCREEN_ID if is_test else home_screen_id
    logging.debug('Publishing home screen %s for community %d as %s', home_screen_id, community_id,
                  publish_home_screen_id)
    with oca_client:
        # Create an instance of the API class
        api_instance = oca.DefaultApi(oca_client)
        community = get_community(community_id)
        service_user = community.main_service_user
        branding_settings = db.get(SolutionBrandingSettings.create_key(service_user))  # type: SolutionBrandingSettings
        keys = [
            CommunityHomeScreen.create_key(community.id, home_screen_id),
            ServiceInfo.create_key(service_user, ServiceIdentity.DEFAULT),
            OpeningHours.create_key(service_user, ServiceIdentity.DEFAULT),
        ]
        home_screen_model, service_info, opening_hours = ndb.get_multi(
            keys)  # type: CommunityHomeScreen, ServiceInfo, OpeningHours
        data = deepcopy(home_screen_model.data)  # take copy to make sure we don't overwrite the model
        bottom_sheet_sections = parse_complex_value(BottomSheetSectionTemplateInstance,
                                                    data['bottom_sheet']['rows'], True)
        default_lang = data['default_language']
        bottom_sheet_rows = [convert_section_template_to_item(row, service_info, opening_hours, default_lang,
                                                              community_id) for row in bottom_sheet_sections]
        if is_test:
            bottom_sheet_rows.extend(extra_sections)

        data['bottom_sheet']['rows'] = [row.to_dict() for row in bottom_sheet_rows if row]
        # call the __deserialize "private" method
        home_screen = api_instance.api_client._ApiClient__deserialize(data, HomeScreen)  # type: HomeScreen
        bottom_sheet = home_screen.bottom_sheet  # type: HomeScreenBottomSheet
        bottom_sheet.header.image = branding_settings.avatar_url
        # Saves the home screen for a community
        api_instance.update_home_screen(community.id, publish_home_screen_id, home_screen=home_screen)
        if not is_test:
            home_screen_model.publish_date = datetime.now()
            home_screen_model.put()


def test_home_screen(community_id, home_screen_id, user_email):
    reset_date = datetime.now() + relativedelta(minutes=15)
    if DEBUG:
        reset_date = datetime.now()
    publish_home_screen(community_id, home_screen_id, is_test=True, extra_sections=[TextSectionTO(
                title='Test version',
                description='This is a test version of the "%s" home screen and it '
                            'will only be accessible until approximately %s' % (home_screen_id, reset_date.isoformat())
            )])
    user_profile = get_user_profile(users.User(user_email))
    key = HomeScreenTestUser.create_key(user_email)
    if user_profile.home_screen_id != TEST_HOME_SCREEN_ID:
        # User his original home screen is reset via a cron
        tester = HomeScreenTestUser(key=key,
                                    reset_date=reset_date,
                                    community_id=user_profile.community_id,
                                    home_screen_id=user_profile.home_screen_id)
        user_profile.home_screen_id = TEST_HOME_SCREEN_ID
        user_profile.version += 1
        user_profile.put()
        update_mobiles(users.User(user_email), user_profile)
    else:
        tester = key.get()
        tester.reset_date = reset_date
    tester.put()


def get_temporary_home_screen(community_id, home_screen_id):
    # type: (int, unicode) -> dict
    community = get_community(community_id)
    key = CommunityHomeScreen.create_key(community_id, home_screen_id)
    home_screen = key.get()  # type: Optional[CommunityHomeScreen]
    if home_screen:
        return home_screen.data

    return HomeScreen(
        version=1,
        bottom_navigation=HomeScreenBottomNavigation(
            buttons=[
                HomeScreenNavigationButton(icon='fa-home',
                                           action='open://' + json.dumps({'action': 'home', 'action_type': None}),
                                           label='$home'),
                HomeScreenNavigationButton(icon='fa-envelope',
                                           action='open://' + json.dumps({'action': 'messages', 'action_type': None}),
                                           label='$messages'),
                HomeScreenNavigationButton(icon='fa-cog',
                                           action='open://' + json.dumps({'action': 'settings', 'action_type': None}),
                                           label='$settings'),
            ]
        ),
        content=HomeScreenContent(type='native',
                                  service_email=community.main_service),
        bottom_sheet=HomeScreenBottomSheet(
            header=HomeScreenBottomSheetHeader(title='$headerTitle',
                                               subtitle=None,
                                               image=None),
            rows=[
                ListSectionTemplate(
                    style=ListSectionStyle.HORIZONTAL,
                    items=[
                        LinkItemTemplate(
                            style=HorizontalLinkListItemStyle.ROUND_BUTTON_WITH_ICON,
                            title='$directions',
                            icon='fa-location-arrow',
                            content=LinkItemAddress()
                        ),
                        LinkItemTemplate(
                            style=HorizontalLinkListItemStyle.ROUND_BUTTON_WITH_ICON,
                            title='$email_verb',
                            content=LinkItemSyncedContent(source=LinkItemSource.SERVICE_INFO_EMAIL)
                        ),
                        LinkItemTemplate(
                            style=HorizontalLinkListItemStyle.ROUND_BUTTON_WITH_ICON,
                            title='$Call',
                            content=LinkItemSyncedContent(source=LinkItemSource.SERVICE_INFO_PHONE)
                        ),
                        LinkItemTemplate(
                            style=HorizontalLinkListItemStyle.ROUND_BUTTON_WITH_ICON,
                            title='$website',
                            content=LinkItemSyncedContent(source=LinkItemSource.SERVICE_INFO_WEBSITE)
                        )
                    ]),
                ListSectionTemplate(items=[
                    LinkItemTemplate(
                        content=LinkItemContentDefault(
                            url='open://' + json.dumps({'action': 'services', 'action_type': None}),
                        ),
                        title='$other_city_services',
                        style=VerticalLinkListItemStyle.BUTTON),
                    OpeningHoursItemTemplate(),
                    LinkItemTemplate(content=LinkItemAddress()),
                    ExpandableItemTemplate(source=ExpandableItemSource.SERVICE_INFO_DESCRIPTION),
                ])]
        ),
        default_language=DEFAULT_LANGUAGE,
        translations={
            DEFAULT_LANGUAGE: {
                'headerTitle': community.name,
                'Call': localize(DEFAULT_LANGUAGE, 'Call'),
                'directions': localize(DEFAULT_LANGUAGE, 'directions'),
                'email_verb': localize(DEFAULT_LANGUAGE, 'email_verb'),
                'home': localize(DEFAULT_LANGUAGE, 'home'),
                'messages': localize(DEFAULT_LANGUAGE, 'messages'),
                'other_city_services': localize(DEFAULT_LANGUAGE, 'other_city_services'),
                'settings': localize(DEFAULT_LANGUAGE, 'settings'),
                'website': localize(DEFAULT_LANGUAGE, 'website'),
            }
        },
    ).to_dict()


def save_temporary_home_screen(community_id, home_screen_id, data):
    # type: (int, unicode, dict) -> dict
    key = CommunityHomeScreen.create_key(community_id, home_screen_id)
    home_screen = key.get() or CommunityHomeScreen(key=key, community_id=community_id)
    home_screen.community_id = community_id
    home_screen.data = data
    home_screen.put()
    return home_screen.data


def get_home_screen_translations():
    languages = ['en', 'nl']
    # Common keys that are used a lot on home screens
    # This way we don't have to translate them every single time for every home screen
    keys = [
        'Call',
        'directions',
        'email_verb',
        'home',
        'messages',
        'more',
        'other_city_services',
        'other_municipality_services',
        'scan',
        'settings',
        'website'
    ]
    return [{
        'key': key,
        'values': {
            language: localize(language, key) for language in languages
        }
    } for key in keys]
