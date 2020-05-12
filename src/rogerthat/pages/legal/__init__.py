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

from datetime import datetime
import os

from babel.dates import format_date
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from rogerthat.templates import get_languages_from_request
from rogerthat.translations import localize
from rogerthat.utils import urlencode

_BASE_DIR = os.path.dirname(__file__)

LANGUAGES = ["en", "nl"]
DOC_PRIVACY_POLICY = "privacy-policy"
DOC_TERMS_SERVICE = "terms-and-conditions-service"
DOC_TERMS = "terms-and-conditions"
# List of docs shown in the /legal page, should only be for normal users (not services)
DOCS = [DOC_PRIVACY_POLICY, DOC_TERMS]
DOC_SETTINGS = {
    DOC_PRIVACY_POLICY: {
        "versions": [
            20180524,
            20171114,
            20120110
        ]
    },
    DOC_TERMS_SERVICE: {
        "versions":  [
            20180524,
            20120110
        ]
    },
    DOC_TERMS: {
        "versions": [
            20180524,
            20120110
        ]
    }
}


def get_current_document_version(document_type):
    return DOC_SETTINGS[document_type]['versions'][0]


def _get_revisions_content(language, doc):
    versions = []
    for version_id in DOC_SETTINGS[doc]["versions"]:
        if version_id == DOC_SETTINGS[doc]["versions"][0]:
            version_name = localize(language, 'current-version')
        else:
            dt = datetime.strptime(str(version_id), '%Y%m%d')
            version_name = format_date(dt, locale=language)

        versions.append({"id": version_id, "name": version_name})

    path = os.path.join(_BASE_DIR, 'assets', language, "revisions.html")
    translation_key = doc
    return template.render(path, {
        'title': localize(language, translation_key),
        'doc': doc,
        'language': language.upper(),
        'versions': versions
    })


def get_version_content(language, doc, version):
    dt = datetime.strptime(str(version), "%Y%m%d")
    version_name = format_date(dt, locale=language)

    path = os.path.join(_BASE_DIR, 'assets', language, "version_%s_%s.html" % (doc, version))
    if language != LANGUAGES[0] and not os.path.exists(path):
        path = os.path.join(_BASE_DIR, 'assets', LANGUAGES[0], "version_%s_%s.html" % (doc, version))

    translation_key = doc
    return template.render(path, {
        'title': localize(language, translation_key),
        'doc': doc,
        'language': language.upper(),
        'current': version == DOC_SETTINGS[doc]["versions"][0],
        'date_modified': version_name
    })


def get_legal_language(lang):
    # convert en_UK to en
    if '_' in lang:
        lang = lang.split('_')[0]
    if lang not in LANGUAGES:
        lang = LANGUAGES[0]
    return lang


class LegalHandler(webapp.RequestHandler):

    def _default_redirect(self, doc):
        self.redirect("/legal?%s" % urlencode((("doc", doc),)))

    def get(self):
        request_langs = get_languages_from_request(self.request)
        language = self.request.GET.get("l", request_langs[0] if request_langs else None)
        if language:
            language = language.lower()
        doc = self.request.GET.get("doc", None)
        mode = self.request.GET.get("mode", None)
        version = self.request.GET.get("version", None)
        color = self.request.GET.get("color", None)
        if color and not color.startswith('#'):
            color = '#' + color

        if version:
            try:
                version = long(version)
            except:
                version = None
        if doc not in DOCS:
            doc = DOC_PRIVACY_POLICY

        supported_language = get_legal_language(language)
        if language != supported_language:
            language = supported_language

        params = {'doc': doc}
        if mode == "revisions":
            params["mode"] = mode
            content = _get_revisions_content(language, doc)
        else:
            if not version:
                version = DOC_SETTINGS[doc]["versions"][0]
            elif version not in DOC_SETTINGS[doc]["versions"]:
                return self._default_redirect(doc)
            params["version"] = version
            content = get_version_content(language, doc, version)

        docs = []
        for d in DOCS:
            translation_key = d
            docs.append({"id": d, "name": localize(language, translation_key)})

        current_url = "/legal?%s" % urlencode(params)

        path = os.path.join(_BASE_DIR, 'assets', LANGUAGES[0], 'index.html')
        self.response.out.write(template.render(path, {"doc": doc,
                                                       "docs": docs,
                                                       "current_url": current_url,
                                                       "language": language.upper(),
                                                       "languages": [l.upper() for l in LANGUAGES],
                                                       "content": content,
                                                       "color": color}))
