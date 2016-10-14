# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import logging

from google.appengine.ext import webapp
from rogerthat.translations import DEFAULT_LANGUAGE
from solutions.common import SOLUTION_COMMON
from solutions.common.consts import UNIT_SYMBOLS
from solutions.common.localizer import translations as common_translations
from solutions.djmatic import SOLUTION_DJMATIC
from solutions.djmatic.localizer import translations as djmatic_translations
from solutions.flex import SOLUTION_FLEX
from solutions.flex.localizer import translations as flex_translations


SOLUTIONS = [SOLUTION_DJMATIC, SOLUTION_FLEX]

translations = dict()
translations[SOLUTION_DJMATIC] = djmatic_translations
translations[SOLUTION_COMMON] = common_translations
translations[SOLUTION_FLEX] = flex_translations

webapp.template.register_template_library('rogerthat.templates.filter')
webapp.template.register_template_library('solutions.templates.filter')


def translate(language, lib, key, suppress_warning=False, _duplicate_backslashes=False, **kwargs):
    if not language:
        language = DEFAULT_LANGUAGE
    if not lib or not key:
        raise ValueError("lib and key are required arguments")
    if not lib in translations:
        raise ValueError("Unknown translation library '%s' requested" % lib)
    library = translations[lib]
    language = language.replace('-', '_')
    if not language in library:
        if '_' in language:
            language = language.split('_')[0]
            if not language in library:
                language = DEFAULT_LANGUAGE
        else:
            language = DEFAULT_LANGUAGE
    if key in library[language]:
        s = library[language][key]
    else:
        if key not in library[DEFAULT_LANGUAGE]:
            if lib != SOLUTION_COMMON:
                return translate(language, SOLUTION_COMMON, key, suppress_warning, **kwargs)
            else:
                raise ValueError("Translation key '%s' not found in library '%s' for default language" % (key, lib))
        if not suppress_warning:
            logging.warn("Translation key '%s' not found in library '%s' for language "
                         "'%s' - fallback to default" % (key, lib, language))
        s = library[DEFAULT_LANGUAGE][key]

    if kwargs:
        s = s % kwargs

    if _duplicate_backslashes:
        s = s.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t').replace("'", "\\'").replace('"', '\\"')

    return s


def translate_unit_symbol(language, unit):
    try:
        return translate(language, SOLUTION_COMMON, UNIT_SYMBOLS[unit])
    except ValueError:
        return UNIT_SYMBOLS[unit]
