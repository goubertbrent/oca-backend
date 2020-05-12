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

from mcfw.properties import unicode_property, long_property, bool_property, typed_property, unicode_list_property


class BrandingTO(object):
    id = unicode_property('1')
    description = unicode_property('2')
    timestamp = long_property('3')
    type = long_property('4')
    created_by_editor = bool_property('5')

    @classmethod
    def from_model(cls, branding):
        """
        Args:
            branding (rogerthat.models.Branding)
        """
        b = cls()
        b.id = branding.hash
        b.description = branding.description
        b.timestamp = branding.timestamp
        b.type = branding.type
        b.created_by_editor = branding.editor_cfg_key is not None
        return b


class ReplacedBrandingsTO(object):
    new_branding = typed_property('new_branding', BrandingTO)
    replaced_branding_hashes = unicode_list_property('replaced_branding_hashes')

    def __init__(self, new_branding=None, replaced_branding_hashes=None):
        # type: (BrandingTO, list[unicode]) -> self
        self.new_branding = new_branding
        self.replaced_branding_hashes = replaced_branding_hashes or []


class UpdatedBrandingTO(object):
    REASON_NEW_TRANSLATIONS = u'new_translations'
    old_id = unicode_property('1')
    new_id = unicode_property('2')

    @classmethod
    def create(cls, old_id, new_id):
        to = cls()
        to.old_id = old_id.decode('utf-8')
        to.new_id = new_id.decode('utf-8')
        return to

    @classmethod
    def from_dict(cls, d):  # d = { old_id : new_id }
        return [cls.create(*i) for i in d.iteritems()]


class BrandingEditorConfigurationTO(object):
    color_scheme = unicode_property('1')
    background_color = unicode_property('2')
    text_color = unicode_property('3')
    menu_item_color = unicode_property('4')
    static_content = unicode_property('5')
    static_content_mode = unicode_property('6')

    @staticmethod
    def fromModel(model):
        to = BrandingEditorConfigurationTO()
        to.color_scheme = model.color_scheme
        to.background_color = model.background_color
        to.text_color = model.text_color
        to.menu_item_color = model.menu_item_color
        to.static_content = model.static_content
        to.static_content_mode = model.static_content_mode
        return to
