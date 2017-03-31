# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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
# @@license_version:1.3@@

import logging

from babel import Locale

from shop.translations import shop_translations

SHOP_DEFAULT_LANGUAGE = u"en"
CURRENCY_SYMBOLS = dict(Locale(SHOP_DEFAULT_LANGUAGE).currency_symbols)
CURRENCIES = dict(Locale(SHOP_DEFAULT_LANGUAGE).currencies)


def shop_translate(lang, key, **kwargs):
    if not lang:
        lang = SHOP_DEFAULT_LANGUAGE
    lang = lang.replace('-', '_')
    if lang not in shop_translations:
        if '_' in lang:
            lang = lang.split('_')[0]
            if lang not in shop_translations:
                lang = SHOP_DEFAULT_LANGUAGE
        else:
            lang = SHOP_DEFAULT_LANGUAGE
    langdict = shop_translations[lang]
    if key not in langdict:
        # Fall back to default language
        if lang != SHOP_DEFAULT_LANGUAGE:
            logging.warn("Shop translation key %s not found for language %s - fallback to default" % (key, lang))
            lang = SHOP_DEFAULT_LANGUAGE
            langdict = shop_translations[lang]
    if key in langdict:
        if kwargs:
            return langdict[key] % kwargs
        return langdict[key]
    logging.error("Shop translation key %s not found in default language - fallback to key" % key)
    return unicode(key) % kwargs


def get_languages():
    return shop_translations.keys()
