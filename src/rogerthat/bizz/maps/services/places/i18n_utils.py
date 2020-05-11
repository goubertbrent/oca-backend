# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
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
# @@license_version:1.6@@

import json
import logging
import os


DEFAULT_LANGUAGE = u'en'
I18N_DIR = os.path.join(os.path.dirname(__file__), 'i18n')

_translations = {}


def _get_translations():
    if _translations:
        return _translations
    for filename in os.listdir(I18N_DIR):
        with open(os.path.join(I18N_DIR, filename)) as f:
            _translations[filename.split('.json')[0]] = json.load(f)
    return _translations


def get_available_languages():
    return _get_translations().keys()


def get_dict_for_language(language):
    translations = _get_translations()
    language = get_supported_locale(language)
    return translations[language]


def get_supported_locale(locale):
    languages = get_available_languages()
    if locale in languages:
        return locale
    language = (locale or '').replace('_', '-')
    if '-' in language:
        language = language.split('-')[0]
    return language if language in languages else DEFAULT_LANGUAGE


def translate(language, key):
    translations = _get_translations()
    language = get_supported_locale(language)
    if key in translations[language]:
        return translations[language][key]

    if key in translations[DEFAULT_LANGUAGE]:
        msg = u'Translation key \'{}\' not found for language \'{}\' - fallback to default'
        logging.warn(msg.format(key, language))
        return translations[DEFAULT_LANGUAGE][key]

    return None
#     msg = u'No translation found for key \'{}\' for default language - fallback to key'
#     logging.error(msg.format(key))
#     return key
