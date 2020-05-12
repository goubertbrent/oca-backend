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

import base64
from PIL import Image

from google.appengine.ext import db

from mcfw.rpc import returns, arguments
from rogerthat.bizz.system import DEFAULT_OCA_QR_CODE_OVERLAY, HAND_ONLY_QR_CODE_OVERLAY, \
    EMPTY_QR_CODE_OVERLAY, LOGO_SIZE, LOGO_POSITION
from rogerthat.dal import parent_key
from rogerthat.models import App, QRTemplate
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.to.app import CreateAppQRTemplateTO
from rogerthat.utils import png, now, parse_color
from rogerthat.utils.transactions import run_in_transaction

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class InvalidQRCodeBodyColorException(ServiceApiException):
    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_QR + 1, "Invalid QR code color specification.")


class InvalidQRDescriptionException(ServiceApiException):
    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_QR + 2, "Invalid QR code description.")


class InvalidQRTemplateSizeException(ServiceApiException):
    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_QR + 3, "Invalid QR code template size.")


class QrTemplateRequiredException(ServiceApiException):
    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_QR + 4, 'At least one QR template must be set')


@returns(QRTemplate)
@arguments(user=users.User, png_stream=str, description=unicode, color=unicode, key_name=unicode)
def store_template(user, png_stream, description, color, key_name=None):
    # Validate color
    try:
        color = parse_color(color)
    except ValueError:
        raise InvalidQRCodeBodyColorException()
    # Validate description
    if not description or not description.strip():
        raise InvalidQRDescriptionException()
    # Validate png
    png_value = png_stream
    if png_stream:
        png_stream = StringIO(png_stream)
        reader = png.Reader(file=png_stream)
        img = reader.read()
        width, height, _, _ = img
        if width < 343 or height < 343:
            raise InvalidQRTemplateSizeException()
    # Store template
    if user:
        parent = parent_key(user)
    else:
        parent = None

    if key_name:
        template = QRTemplate(key=db.Key.from_path(QRTemplate.kind(), key_name, parent=parent),
                              description=description, body_color=list(color), timestamp=now())
    else:
        template = QRTemplate(parent=parent, description=description, body_color=list(color), timestamp=now())

    if png_value:
        template.blob = db.Blob(png_value)
    template.put()
    return template


def get_app_qr_templates(app_id):
    from rogerthat.bizz.app import get_app
    app = get_app(app_id)
    return QRTemplate.get_by_key_name(app.qrtemplate_keys)


def store_app_qr_template(app_id, data):
    """
    Args:
        app_id (unicode)
        data (rogerthat.to.app.CreateAppQRTemplateTO)
    """

    from rogerthat.bizz.app import get_app

    def trans():
        app = get_app(app_id)
        picture = base64.b64decode(data.file)
        key_name = QRTemplate.create_key_name(app_id, data.description)
        template = store_template(None, picture, data.description, data.body_color, key_name)
        if data.is_default:
            app.qrtemplate_keys.insert(0, key_name)
        else:
            app.qrtemplate_keys.append(template.key().name())
        app.put()
        return template

    template = run_in_transaction(trans, xg=True)
    return template, data.is_default


def create_default_qr_template(app, description=u'Default QR template', color=u'#000', image_content=None):
    """Create default qr template for an app

    Args:
        app (rogerthat.models.App)
        description (basestring)
        color (basestring)
        image_content (str) content of the image
    """
    if not app.qrtemplate_keys or not QRTemplate.get_by_key_name(app.qrtemplate_keys[0]):
        default_data = CreateAppQRTemplateTO()
        default_data.is_default = True
        default_data.description = description
        default_data.body_color = color

        if image_content:
            default_data.file = u'%s' % base64.b64encode(image_content)
        elif app.type == App.APP_TYPE_CITY_APP:
            default_data.file = u'%s' % base64.b64encode(DEFAULT_OCA_QR_CODE_OVERLAY)
        else:
            default_data.file = u'%s' % base64.b64encode(HAND_ONLY_QR_CODE_OVERLAY)

        return store_app_qr_template(app.app_id, default_data)


def create_default_qr_template_from_logo(app_id, logo_content):
    from rogerthat.bizz.app import get_app
    app = get_app(app_id)

    logo_content = base64.b64decode(logo_content)
    # put the logo on the empty overlay in place of rogerthat "hands only" logo
    logo_image = Image.open(StringIO(logo_content)).resize(LOGO_SIZE, Image.ANTIALIAS)
    logo_image_with_background = Image.new('RGBA', logo_image.size, (255, 255, 255, 255))
    logo_image_with_background.paste(logo_image, (0, 0), mask=logo_image)
    qr_image = Image.open(StringIO(EMPTY_QR_CODE_OVERLAY))
    qr_image.paste(logo_image_with_background, LOGO_POSITION)
    out = StringIO()
    qr_image.save(out, 'png')

    return create_default_qr_template(app, image_content=out.getvalue())


def delete_app_qr_template(app_id, key_name):
    from rogerthat.bizz.app import get_app
    app = get_app(app_id)
    if key_name in app.qrtemplate_keys:
        if len(app.qrtemplate_keys) <= 1:
            raise QrTemplateRequiredException()
        app.qrtemplate_keys.remove(key_name)
        template = QRTemplate.get_by_key_name(key_name)
        if template:
            template.delete()
        app.put()
