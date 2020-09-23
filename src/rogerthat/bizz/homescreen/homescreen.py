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

import logging

from google.appengine.api.app_identity.app_identity import get_application_id
from google.appengine.ext import db
from urllib3.contrib.appengine import AppEngineManager

# TODO communities: move the api client to a separate repo instead and use pip to install this instead
# otherwise we'll have the same files in the repo twice
import oca
from oca import HomescreenBottomNavigation, HomescreenNavigationButton, HomescreenBottomSheet, \
    HomescreenBottomSheetHeader, HomeScreen, HomescreenContent
from rogerthat.bizz.communities.communities import get_community
from rogerthat.consts import DEBUG
from rogerthat.models import ServiceIdentity
from rogerthat.models.maps import MapService
from rogerthat.models.settings import ServiceInfo
from rogerthat.to.maps import ListSectionTO, ListSectionStyle, LinkListSectionItemTO, LinkListItemStyle
from rogerthat.translations import localize, DEFAULT_LANGUAGE
from solutions.common.models import SolutionBrandingSettings

configuration = oca.Configuration(
    host='http://localhost:8333/api' if DEBUG else 'https://oca-dot-%s.ew.r.appspot.com/api' % get_application_id(),
)

if DEBUG:
    configuration.api_key = {'X-Appengine-Inbound-Appid': get_application_id()}

oca_client = oca.ApiClient(configuration)
oca_client.rest_client.pool_manager = AppEngineManager()


def maybe_update_homescreen(map_service, community_id):
    # type: (MapService, long) -> None
    community = get_community(community_id)
    if community.main_service == map_service.service_user.email():
        logging.debug('Updating homescreen for community %s(%s)', community.name, community.id)
        update_homescreen(map_service, community_id)


def update_homescreen(service, community_id):
    # type: (MapService, long) -> None
    with oca_client:
        # Create an instance of the API class
        api_instance = oca.DefaultApi(oca_client)

        rows = []
        service_user = service.service_user
        service_info = ServiceInfo.create_key(service_user, ServiceIdentity.DEFAULT).get()  # type: ServiceInfo
        branding_settings = db.get(SolutionBrandingSettings.create_key(service_user))  # type: SolutionBrandingSettings

        horiz_section = ListSectionTO()
        horiz_section.items = [item.item for item in service.horizontal_items]
        horiz_section.style = ListSectionStyle.HORIZONTAL
        rows.append(horiz_section.to_dict())

        community_services_btn = LinkListSectionItemTO()
        community_services_btn.url = 'open://{"action_type":null, "action": "community_services"}'
        community_services_btn.icon = None
        community_services_btn.icon_color = None
        # TODO: translation (+ could also be "andere gemeentediensten")
        other_city_services = 'other_city_services'
        community_services_btn.title = '$' + other_city_services
        community_services_btn.style = LinkListItemStyle.BUTTON

        vertical_section = ListSectionTO()
        vertical_section.style = ListSectionStyle.VERTICAL
        vertical_section.items = [community_services_btn] + [item.item for item in service.vertical_items]
        rows.append(vertical_section.to_dict())

        languages = ['en', 'nl']
        keys = ['home', 'messages', 'scan', 'more', other_city_services]
        translations = {language: {key: localize(language, key) for key in keys} for language in languages}
        home_screen = HomeScreen(
            bottom_navigation=HomescreenBottomNavigation(
                buttons=[
                    HomescreenNavigationButton(icon='fa-home', label='$home',
                                               action='open://{"action_type":null,"action":"home"}'),
                    HomescreenNavigationButton(icon='fa-envelope', label='$messages',
                                               action='open://{"action_type":null,"action":"messages"}',
                                               badge_key='messages'),
                    HomescreenNavigationButton(icon='fa-qrcode', label='$scan',
                                               action='open://{"action_type":null,"action":"scan"}'),
                    HomescreenNavigationButton(icon='fa-ellipsis-h', label='$more',
                                               action='open://{"action_type":null,"action":"settings"}'),
                ]),
            content=HomescreenContent(type='embedded_app', embedded_app='homescreen-vilvoorde'),
            bottom_sheet=HomescreenBottomSheet(
                header=HomescreenBottomSheetHeader(title=service_info.name,
                                                   subtitle=None,
                                                   image=branding_settings.avatar_url),
                rows=rows
            ),
            default_language=DEFAULT_LANGUAGE,
            translations=translations
        )
        # Saves the homescreen for a community
        api_instance.update_home_screen(community_id, home_screen=home_screen)
