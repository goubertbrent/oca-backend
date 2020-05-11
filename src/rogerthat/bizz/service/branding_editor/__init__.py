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

import base64
import os.path
from zipfile import ZipFile, ZIP_DEFLATED

from google.appengine.ext import db
from google.appengine.ext.webapp import template

from mcfw.imaging import recolor_png
from mcfw.properties import azzert
from mcfw.rpc import arguments, returns
from rogerthat.bizz.branding import store_branding_zip
from rogerthat.models import Branding, BrandingEditorConfiguration
from rogerthat.rpc import users

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

COLOR_WHITE = 'FFFFFF'
COLOR_BLACK = '000000'

LOGO_WIDTH = 320
LOGO_HEIGHT = 120
LOGO_MAX_SIZE = 102400  # 100kb

@returns(Branding)
@arguments(service_user=users.User, description=unicode, color_scheme=unicode, background_color=unicode,
           text_color=unicode, menu_item_color=unicode, show_header=bool, static_content_mode=unicode,
           static_content=unicode, logo=unicode)
def generate_branding(service_user, description, color_scheme, background_color=None, text_color=None,
                      menu_item_color=None, show_header=False, static_content_mode="disabled", static_content="",
                      logo=None):

    def trans(branding_key, params):
        branding = Branding.get(branding_key)

        editor_cfg = BrandingEditorConfiguration(key=BrandingEditorConfiguration.create_key(branding.hash, service_user))
        editor_cfg.color_scheme = params['color_scheme']
        editor_cfg.background_color = params['background_color']
        editor_cfg.text_color = params['text_color']
        editor_cfg.menu_item_color = params['menu_item_color']
        editor_cfg.static_content = params['static_content']
        editor_cfg.static_content_mode = static_content_mode
        editor_cfg.put()

        branding.editor_cfg_key = str(editor_cfg.key())
        branding.put()
        return branding

    branding_html, params = render_branding_html(color_scheme, background_color, text_color, menu_item_color, show_header, static_content)
    dir_name = os.path.dirname(__file__)
    zip_ = ZipFile(StringIO(), 'w', compression=ZIP_DEFLATED)
    zip_.writestr('branding.html', branding_html.encode('utf8'))
    if logo:
        _meta, img_b64 = logo.split(',')
        image_bytes = base64.b64decode(img_b64)
        zip_.writestr('logo.jpg', image_bytes)
    else:
        zip_.write(os.path.join(dir_name, 'logo.jpg'), 'logo.jpg')
    with open(os.path.join(dir_name, 'frame.png'), 'r') as f:
        zip_.writestr('frame.png', recolor_png(f.read(), webcolor_to_color_tuple(COLOR_BLACK), webcolor_to_color_tuple(params['background_color'])))

    branding = store_branding_zip(service_user, zip_, description)
    xg_on = db.create_transaction_options(xg=True)
    return db.run_in_transaction_options(xg_on, trans, branding.key(), params)


@returns(tuple)
@arguments(color_scheme=unicode, background_color=unicode, text_color=unicode, menu_item_color=unicode, show_header=bool, static_content=unicode)
def render_branding_html(color_scheme, background_color=None, text_color=None, menu_item_color=None, show_header=False, static_content=""):
    azzert(color_scheme in Branding.COLOR_SCHEMES)

    if background_color is None:
        background_color = COLOR_BLACK if color_scheme == Branding.COLOR_SCHEME_DARK else COLOR_WHITE
    if text_color is None:
        text_color = Branding.DEFAULT_MENU_ITEM_COLORS[color_scheme]
    if menu_item_color is None:
        menu_item_color = Branding.DEFAULT_MENU_ITEM_COLORS[color_scheme]

    params = {'color_scheme' : color_scheme,
              'background_color' : background_color,
              'text_color' : text_color,
              'menu_item_color' : menu_item_color,
              'show_header' : show_header,
              'static_content': static_content}
    # Warning: resources of the branding_editor are cached by the client. Don't forget to bump the version of the
    # branding_editor URLs in /static/parts/branding.html when updating branding.tmpl, frame.png or logo.jpg
    return template.render(os.path.join(os.path.dirname(__file__), 'branding.tmpl'), params), params



@returns(tuple)
@arguments(webcolor=unicode)
def webcolor_to_color_tuple(webcolor):
    # Validate input
    color = webcolor.upper()
    color = color.replace('#', '')
    test = color
    for digit in "0123456789ABCDEF":
        test = test.replace(digit, '')
    azzert(not test, "Invalid color %s" % webcolor)
    azzert(len(color) == 6, "Invalid color %s" % webcolor)

    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


@returns(BrandingEditorConfiguration)
@arguments(service_user=users.User, branding_hash=unicode)
def get_configuration(service_user, branding_hash):
    return db.get(BrandingEditorConfiguration.create_key(branding_hash, service_user))
