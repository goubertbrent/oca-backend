# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

from __future__ import unicode_literals

from solutions import translate as common_translate, SOLUTION_COMMON
from solutions.common.bizz import SolutionModule
from solutions.common.bizz.loyalty import joyn_supported


OTHER_LANGUAGES = ['nl']


# modules related media per language (tutorial videos...etc)
MEDIA = {
    'nl': {
        SolutionModule.BROADCAST: {
            'video_id': '5NvAKVnbEqI',
            'tutorial_video_id': '5NvAKVnbEqI',
        },
        SolutionModule.LOYALTY: {
            'video_id': 'WRwNCNtIQG4',
            'tutorial_video_id': 'WRwNCNtIQG4',
        },
        SolutionModule.ORDER: {
            'video_id': 'hHOkurV4IIE',
            'tutorial_video_id': 'hHOkurV4IIE',
        },
        SolutionModule.RESTAURANT_RESERVATION: {
            'video_id': '7aFdU2wyTkM',
            'tutorial_video_id': '7aFdU2wyTkM',
        }
    }
}


class Functionality(object):

    def __init__(self, country, language, activated_modules, name):
        self.country = country
        self.language = language
        self.activated_modules = activated_modules
        self.name = name

    def translate(self, key, fallback=None):
        try:
            return common_translate(self.language, SOLUTION_COMMON, key)
        except (KeyError, ValueError):
            return fallback or key

    @property
    def title(self):
        if self.name == SolutionModule.BROADCAST:
            return self.translate('News & actions')
        elif self.name == SolutionModule.ORDER:
            return self.translate('e-shop')
        elif self.name == SolutionModule.SANDWICH_BAR:
            return self.translate('order-sandwich')
        elif self.name == SolutionModule.RESTAURANT_RESERVATION:
            return self.translate('reservations-menu')
        elif self.name == SolutionModule.MENU:
            return self.translate('menu-card')
        elif self.name == SolutionModule.APPOINTMENT:
            return self.translate('appointments')
        elif self.name == SolutionModule.REPAIR:
            return self.translate('repairs')
        elif self.name == SolutionModule.DISCUSSION_GROUPS:
            return self.translate('group-chat')
        elif self.name == SolutionModule.JOYN:
            return self.translate('joyn-loyalty')
        elif self.name == SolutionModule.LOYALTY:
            if self.is_oca_terminal():
                return self.translate('oca-terminal')
            return self.translate('oca-loyalty')
        else:
            translation = self.translate(self.name)
            if translation == self.name:
                return self.translate(self.name.replace('_', '-'))
            return translation

    def is_oca_terminal(self):
        if self.name == SolutionModule.LOYALTY:
            if self.activated_modules:
                if SolutionModule.JOYN in self.activated_modules:
                    return True
                if self.country == "BE":
                    if SolutionModule.LOYALTY not in self.activated_modules \
                            or self.activated_modules[SolutionModule.LOYALTY].timestamp > 0:
                        return True
        return False

    @property
    def description(self):
        if self.is_oca_terminal():
            return self.translate('oca-terminal-description')
        return self.translate('module-description-%s' % self.name)

    @property
    def screenshot_image(self):
        name = self.name
        if name == SolutionModule.DISCUSSION_GROUPS:
            name = SolutionModule.ASK_QUESTION
        return '/static/images/solutions/func_%s.jpg' % name

    @property
    def settings_section(self):
        if self.name == SolutionModule.ASK_QUESTION:
            return 'inbox'
        elif self.name == SolutionModule.HIDDEN_CITY_WIDE_LOTTERY:
            return SolutionModule.LOYALTY

    @property
    def media(self):
        languages_media = {
            'en': {
                'screenshot_image': self.screenshot_image
            }}

        if not self.is_oca_terminal():
            for language in OTHER_LANGUAGES:
                default_media = MEDIA.get(language)
                if default_media:
                    module_media = default_media.get(self.name)
                    if module_media:
                        languages_media[language] = module_media

        return languages_media

    def to_dict(self):
        return {
            'name': self.name,
            'title': self.title,
            'settings_section': self.settings_section,
            'description': self.description,
            'media': self.media
        }


def sort_modules(name):
    if name == SolutionModule.BROADCAST:
        return 0
    return name


def get_functionalities(country, language, my_modules, activated_modules, app_ids):
    # we need the broadcast module to be the first
    modules = sorted(SolutionModule.FUNCTIONALITY_MODULES, key=sort_modules)
    functionalities = [Functionality(country, language, activated_modules, module) for module in modules]
    info = {
        func.name: func.to_dict() for func in functionalities
    }

    if SolutionModule.CITY_APP in my_modules:
        modules.remove(SolutionModule.LOYALTY)
        del info[SolutionModule.LOYALTY]
        modules.remove(SolutionModule.JOYN)
        del info[SolutionModule.JOYN]

    elif SolutionModule.HIDDEN_CITY_WIDE_LOTTERY in modules:
        modules.remove(SolutionModule.HIDDEN_CITY_WIDE_LOTTERY)
        del info[SolutionModule.HIDDEN_CITY_WIDE_LOTTERY]

    if not joyn_supported(country, modules, app_ids):
        modules.remove(SolutionModule.JOYN)
        del info[SolutionModule.JOYN]

    return modules, info
