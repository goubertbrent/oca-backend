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

import logging
import os

import jinja2
from google.appengine.ext.webapp import template
from jinja2 import StrictUndefined

from mcfw.rpc import returns, arguments
from rogerthat import consts
from rogerthat.settings import get_server_settings
from rogerthat.templates.jinja_extensions import TranslateExtension
from rogerthat.translations import DEFAULT_LANGUAGE
from solutions import get_supported_languages

TEMPLATES_DIR = os.path.dirname(__file__)
_SUPPORTED_LANGUAGES = [d for d in os.listdir(TEMPLATES_DIR) if os.path.isdir(os.path.join(TEMPLATES_DIR, d))]
_CONSTS = dict(((name, getattr(consts, name)) for name in dir(consts) if name.upper() == name))

JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__))]),
                                       extensions=[TranslateExtension],
                                       undefined=StrictUndefined)


@returns(unicode)
@arguments(template_name=str, languages=[str], variables=dict, category=unicode)
def render(template_name, languages, variables, category=""):
    logging.info("Rendering %s for languages %s" % (template_name, languages))
    variables = dict(variables)
    variables.update(_CONSTS)
    variables["BASE_URL"] = get_server_settings().baseUrl
    variables["INCLUDE_ROGERTHAT_DOT_NET"] = True
    if not languages:
        languages = list()
    languages.append(DEFAULT_LANGUAGE)
    logging.debug("Supported languages: %s" % _SUPPORTED_LANGUAGES)
    for lang in languages:
        lang = lang.replace('-', '_')
        file_name = os.path.join(TEMPLATES_DIR, lang, category, "%s.tmpl" % template_name)
        if lang in _SUPPORTED_LANGUAGES and os.path.exists(file_name):
            return template.render(file_name, variables)
        if '_' in lang:
            lang = lang.split('_')[0]
            file_name = os.path.join(TEMPLATES_DIR, lang, category, "%s.tmpl" % template_name)
            if lang in _SUPPORTED_LANGUAGES and os.path.exists(file_name):
                return template.render(file_name, variables)
    raise NotImplementedError("Template not found!")


@returns([str])
@arguments(header=unicode)
def get_languages_from_header(header):
    if not header:
        return [DEFAULT_LANGUAGE]
    try:
        languages = list()
        for item in header.split(','):
            items = item.split(';')
            lang = items[0]
            splitted = lang.split('-')
            if len(splitted) == 2:
                lang = '%s_%s' % (splitted[0].lower(), splitted[1].upper())

            qualifier = 1.0
            if len(items) > 1:
                ext = items[1].split('=')
                if len(ext) == 2 and ext[0] == 'q':
                    qualifier = float(ext[1])
            languages.append((qualifier, str(lang).strip()))

        return [i[1] for i in sorted(languages, reverse=True)]
    except:
        logging.exception("Could not parse language header.")
        return [DEFAULT_LANGUAGE]


@returns([str])
@arguments(request=object)
def get_languages_from_request(request):
    return get_languages_from_header(request.headers.get('Accept-Language', None))


def get_language_from_request(request):
    langs = get_languages_from_request(request)
    supported = get_supported_languages()
    for lang in langs:
        simple_lang = lang.split('_')[0]
        if lang in supported:
            return lang
        if simple_lang in supported:
            return simple_lang
    return DEFAULT_LANGUAGE
