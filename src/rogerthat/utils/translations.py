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

from rogerthat.translations import localize


def localize_app_translation(language, translation_key, app_id, **kwargs):
    """
        Uses custom app translations to translate a string.
        Falls back to the normal translations if no custom translation is found.
    Args:
        language (basestring)
        translation_key (basestring)
        app_id (basestring)
        **kwargs: keyword arguments
    Returns:
        unicode
    """
    from rogerthat.dal.app import get_app_translations
    translations = get_app_translations(app_id) if app_id else None
    if translations:
        translation = translations.get_translation(language, translation_key, **kwargs)
        if translation:
            return translation
    return localize(language, translation_key, **kwargs)
