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
import os.path

import webapp2

from mcfw.imaging import recolor_png
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.service.branding_editor import render_branding_html, generate_branding, COLOR_BLACK, \
    webcolor_to_color_tuple, get_configuration
from rogerthat.dal.service import get_default_service_identity
from rogerthat.models import Branding
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.to.branding import BrandingEditorConfigurationTO


class BrandingEditorPreviewHandler(webapp2.RequestHandler):

    def get(self, version, page):
        try:
            if int(version) > 0:
                self.response.headers['Cache-Control'] = "public, max-age=31536000"  # Cache forever (1 year)
        except:
            self.error(404)
            return
        if page not in ('branding.html', 'logo.jpg', 'frame.png'):
            logging.warning("%s not found in branding editor" % page)
            self.error(404)
            return
        _, extension = os.path.splitext(page.lower())
        if extension in (".jpg", ".jpeg"):
            self.response.headers['Content-Type'] = "image/jpeg"
        elif extension == ".png":
            self.response.headers['Content-Type'] = "image/png"
        elif extension == ".css":
            self.response.headers['Content-Type'] = "text/css"

        if page == "branding.html":
            content, _ = render_branding_html(self.request.get("color_scheme", Branding.COLOR_SCHEME_DARK),
                                              self.request.get("background_color", "000000"),
                                              self.request.get("text_color", "FFFFFF"),
                                              self.request.get("menu_item_color", "FFFFFF"),
                                              self.request.get("show_header", "false") == "true")
            logging.debug("branding.html: %s" % content)
        else:
            with open(os.path.join(os.path.dirname(__file__), page)) as f:
                content = f.read()
            target_color = self.request.get("color")
            if target_color and target_color != COLOR_BLACK:
                logging.debug("Re-coloring PNG to %s" % str(webcolor_to_color_tuple(target_color)))
                content = recolor_png(content, webcolor_to_color_tuple(COLOR_BLACK), webcolor_to_color_tuple(target_color))

        if self.request.get('xrender', 'false') == 'true':
            from lxml import html, etree
            doc = html.fromstring(content)
            service_identity = None
            for elem in doc.xpath("//nuntiuz_identity_name"):
                service_identity = service_identity or get_default_service_identity(users.get_current_user())
                parent = elem.getparent()
                elem.drop_tree()
                parent.text = service_identity.name
            self.response.out.write(etree.tostring(doc))  # @UndefinedVariable
        else:
            self.response.out.write(content)


@rest('/mobi/service/branding/editor/save', 'post')
@returns(ReturnStatusTO)
@arguments(description=unicode, color_scheme=unicode, background_color=unicode, text_color=unicode,
           menu_item_color=unicode, show_header=bool, static_content_mode=unicode, static_content=unicode,
           logo=unicode)
def branding_editor_save(description, color_scheme, background_color, text_color, menu_item_color, show_header,
                         static_content_mode, static_content, logo):
    try:
        branding = generate_branding(users.get_current_user(), description, color_scheme, background_color or None,
                                     text_color or None, menu_item_color or None, show_header, static_content_mode,
                                     static_content, logo)
        logging.debug("Generated branding: %s" % branding.key().name())
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as be:
        logging.exception("Failed to generate branding with branding designer")
        return ReturnStatusTO.create(False, "Failed to create branding (%s)" % be.message)


@rest("/mobi/service/branding/editor/cfg", "get")
@returns(BrandingEditorConfigurationTO)
@arguments(branding_hash=unicode)
def branding_editor_configuration(branding_hash):
    model = get_configuration(users.get_current_user(), branding_hash)
    return BrandingEditorConfigurationTO.fromModel(model)
