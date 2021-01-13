#!/usr/bin/python
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

# WARNING: this is a generated file - DO NOT MODIFY
import json
import logging

__all__ = ['localize', 'SUPPORTED_LANGUAGES']

from os import listdir

from os.path import join, dirname

DEFAULT_LANGUAGE = "en"


def localize(lang, key, language_fallback=True, **kwargs):
    if not lang:
        lang = DEFAULT_LANGUAGE
    lang = lang.replace('-', '_')
    if lang not in D:
        if '_' in lang:
            lang = lang.split('_')[0]
            if lang not in D:
                if not language_fallback:
                    return None
                lang = DEFAULT_LANGUAGE
        elif language_fallback:
            lang = DEFAULT_LANGUAGE
        else:
            return None
    langdict = D[lang]
    if key not in langdict:
        if not language_fallback:
            return None
        # Fall back to default language
        if lang != DEFAULT_LANGUAGE:
            logging.warn("Translation key %s not found in language %s - fallback to default" % (key, lang))
            lang = DEFAULT_LANGUAGE
            langdict = D[lang]
    if key in langdict:
        return langdict[key] % kwargs
    logging.warn("Translation key %s not found in default language. Fallback to key" % key)
    return unicode(key) % kwargs


def _load_translations():
    all_translations = {}
    translations_dir = join(dirname(__file__), 'i18n')
    for filename in listdir(translations_dir):
        language = filename.split('.json')[0]
        translation_file = join(translations_dir, filename)
        with open(translation_file) as f:
            all_translations[language] = json.load(f)
    return all_translations


D = _load_translations()
SUPPORTED_LANGUAGES = D.keys()
