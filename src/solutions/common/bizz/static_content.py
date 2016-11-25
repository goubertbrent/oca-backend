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

import base64
from contextlib import closing
import logging
from types import NoneType
from zipfile import ZipFile, ZIP_DEFLATED

from google.appengine.ext import db
from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments
from rogerthat.dal import put_and_invalidate_cache, parent_key
from rogerthat.exceptions.branding import BrandingValidationException
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException, BusinessException
from rogerthat.utils.channel import send_message
from rogerthat.utils.transactions import run_in_transaction
from solutions import translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import broadcast_updates_pending, put_branding
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionSettings
from solutions.common.models.static_content import SolutionStaticContent
from solutions.common.to import SolutionStaticContentTO


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


@returns(NoneType)
@arguments(service_user=users.User, static_content=SolutionStaticContentTO)
def put_static_content(service_user, static_content):
    try:
        branding_hash = store_static_content_branding(service_user, static_content.background_color,
                                                      static_content.text_color, static_content.html_content,
                                                      static_content.icon_label)
    except BrandingValidationException:
        raise
    except ServiceApiException:
        logging.exception('Failed to store static content branding', exc_info=True)
        raise BusinessException(translate(get_solution_settings(service_user).main_language, SOLUTION_COMMON,
                                          'error-occured-unknown-try-again'))

    def trans():
        sln_settings = get_solution_settings(service_user)
        new_coords = map(int, [static_content.position.x, static_content.position.y, static_content.position.z])
        if static_content.id is MISSING or static_content.id is None:
            sc = SolutionStaticContent(parent=parent_key(service_user, SOLUTION_COMMON), deleted=False)
            sc.old_coords = new_coords
        else:
            sc = SolutionStaticContent.get(SolutionStaticContent.create_key(service_user, static_content.id))
            if sc.old_coords != new_coords and sc.provisioned:
                sc.old_coords = sc.coords
        sc.icon_label = static_content.icon_label
        sc.icon_name = static_content.icon_name
        sc.text_color = static_content.text_color
        sc.background_color = static_content.background_color
        sc.html_content = static_content.html_content
        sc.sc_type = SolutionStaticContent.TYPE_OWN
        sc.visible = static_content.visible
        sc.branding_hash = branding_hash
        sc.provisioned = False
        sc.coords = new_coords
        sc.put()

        sln_settings.updates_pending = True
        put_and_invalidate_cache(sc, sln_settings)
        return sln_settings

    sln_settings = run_in_transaction(trans, True)

    send_message(service_user, u"solutions.common.service_menu.updated")
    broadcast_updates_pending(sln_settings)


@returns(NoneType)
@arguments(service_user=users.User, static_content_id=(int, long))
def _delete_static_content(service_user, static_content_id):
    sln_settings, sc = db.get((SolutionSettings.create_key(service_user),
                               SolutionStaticContent.create_key(service_user, static_content_id)))

    def trans():
        sc.provisioned = False
        sc.deleted = True
        sln_settings.updates_pending = True
        db.put([sln_settings, sc])
        return sln_settings

    sln_settings = run_in_transaction(trans, True)
    send_message(service_user, u"solutions.common.service_menu.updated")
    broadcast_updates_pending(sln_settings)


@returns(NoneType)
@arguments(service_user=users.User, static_content_id=(int, long))
def delete_static_content(service_user, static_content_id):
    users.set_user(service_user)
    try:
        _delete_static_content(service_user, static_content_id)
    finally:
        users.clear_user()


@returns(unicode)
@arguments(service_user=users.User, background_color=unicode, text_color=unicode, html_content=unicode,
           icon_label=unicode)
def store_static_content_branding(service_user, background_color, text_color, html_content, icon_label):
    with closing(StringIO()) as new_zip_stream:
        with closing(ZipFile(new_zip_stream, 'w', compression=ZIP_DEFLATED)) as zip_:
            html = u"""<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</head>
<style>
    img {
         max-width: 100%%;
         height: auto;
    }
</style>
<body style="background-color: %s; color: %s;">%s</body>
</html>""" % (background_color, text_color, html_content)

            zip_.writestr('app.html', html.encode('utf-8'))

        branding_content = new_zip_stream.getvalue()

    branding_hash = put_branding(u"Static content: %s" % icon_label, base64.b64encode(branding_content)).id
    return branding_hash
