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
from types import NoneType

from google.appengine.api import images
from google.appengine.ext import db, deferred

from mcfw.rpc import returns, arguments
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.rpc import users
from rogerthat.rpc.models import TempBlob
from rogerthat.utils import now
from rogerthat.utils.channel import send_message
from rogerthat.utils.transactions import run_in_xg_transaction
from rogerthat.utils.zip_utils import replace_file_in_zip_blob
from solutions.common.bizz import _get_location, broadcast_updates_pending
from solutions.common.dal import get_solution_settings, get_solution_logo, get_solution_main_branding, \
    get_solution_settings_or_identity_settings
from solutions.common.models import SolutionLogo, SolutionAvatar, SolutionSettings, \
    SolutionBrandingSettings
from solutions.common.utils import is_default_service_identity

SLN_LOGO_WIDTH = 640
SLN_LOGO_HEIGHT = 240
SLN_LOGO_MAX_SIZE = 102400  # 100 kB
SLN_AVATAR_WIDTH = 150
SLN_AVATAR_HEIGHT = 150
SLN_AVATAR_MAX_SIZE = 51200  # 50 kB


@returns(bool)
@arguments(service_user=users.User, service_identity=unicode, name=unicode, description=unicode, opening_hours=unicode, address=unicode,
           phone_number=unicode, facebook_page=unicode, facebook_name=unicode, facebook_action=unicode,
           currency=unicode, search_enabled=bool, search_keywords=unicode, timezone=unicode, events_visible=bool,
           email_address=unicode, inbox_email_reminders=bool, iban=unicode, bic=unicode)
def save_settings(service_user, service_identity, name, description=None, opening_hours=None, address=None, phone_number=None,
                  facebook_page=None, facebook_name=None, facebook_action=None, currency=None, search_enabled=True,
                  search_keywords=None, timezone=None, events_visible=None, email_address=None, inbox_email_reminders=None,
                  iban=None, bic=None):
    address_geocoded = True
    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
    sln_i_settings.name = name
    sln_i_settings.description = description
    sln_i_settings.opening_hours = opening_hours
    sln_i_settings.phone_number = phone_number

    if email_address and email_address != service_user.email():
        sln_i_settings.qualified_identifier = email_address
    else:
        sln_i_settings.qualified_identifier = None

    if facebook_page is not None:
        if sln_settings.facebook_page != facebook_page:
            send_message(service_user, u"solutions.common.settings.facebookPageChanged", facebook_page=facebook_page)
    sln_settings.facebook_page = facebook_page
    sln_settings.facebook_name = facebook_name if facebook_page else ""
    sln_settings.facebook_action = facebook_action
    if currency is not None:
        sln_settings.currency = currency
    sln_settings.search_enabled = search_enabled
    sln_i_settings.search_keywords = search_keywords
    if address and sln_i_settings.address != address:
        sln_i_settings.address = address
        try:
            lat, lon = _get_location(address)
            sln_i_settings.location = db.GeoPt(lat, lon)
        except:
            address_geocoded = False
            logging.warning("Failed to resolve address: %s" % sln_i_settings.address, exc_info=1)
    if timezone is not None:
        if sln_settings.timezone != timezone:
            send_message(service_user, u"solutions.common.settings.timezoneChanged")
        sln_settings.timezone = timezone

    if events_visible is not None:
        sln_settings.events_visible = events_visible

    if inbox_email_reminders is not None:
        sln_i_settings.inbox_email_reminders_enabled = inbox_email_reminders

    sln_settings.iban = iban
    sln_settings.bic = bic

    sln_settings.updates_pending = True
    if not is_default_service_identity(service_identity):
        sln_i_settings.put()
    sln_settings.put()

    broadcast_updates_pending(sln_settings)

    return address_geocoded


def _temp_blob_to_bytes(tmp_blob_key, x1, y1, x2, y2, width, height, max_size, substitution_color):
    tb = TempBlob.get(tmp_blob_key)
    quality = 100
    color = int('0x%s' % substitution_color, 0)
    while True:
        img = images.Image(str(tb.blob))
        img.crop(x1, y1, x2, y2)
        img.resize(width, height)
        jpg_bytes = img.execute_transforms(images.JPEG, quality, transparent_substitution_rgb=color)
        if len(jpg_bytes) <= max_size:
            break
        quality -= 5
        logging.debug("transforming TempBlob with quality: %s" % quality)
    return jpg_bytes


@returns(NoneType)
@arguments(service_user=users.User, tmp_avatar_key=unicode,
           x1=(float, int), y1=(float, int), x2=(float, int), y2=(float, int))
def set_avatar(service_user, tmp_avatar_key, x1, y1, x2, y2):
    logging.info('%s: Saving avatar' % service_user.email())
    branding_settings = SolutionBrandingSettings.get(SolutionBrandingSettings.create_key(service_user))
    jpg_bytes = _temp_blob_to_bytes(tmp_avatar_key, x1, y1, x2, y2, SLN_AVATAR_WIDTH, SLN_AVATAR_HEIGHT,
                                    SLN_AVATAR_MAX_SIZE, branding_settings.background_color)

    def trans():
        avatar_key = SolutionAvatar.create_key(service_user)
        avatar, branding_settings, sln_settings = db.get((avatar_key,
                                                          SolutionBrandingSettings.create_key(service_user),
                                                          SolutionSettings.create_key(service_user)))
        avatar = avatar or SolutionAvatar(key=avatar_key)
        avatar.picture = db.Blob(jpg_bytes)
        avatar.published = False

        sln_settings.updates_pending = True
        branding_settings.modification_time = now()

        put_and_invalidate_cache(avatar, sln_settings, branding_settings)

        return sln_settings

    sln_settings = run_in_xg_transaction(trans)
    send_message(sln_settings.service_user, 'solutions.common.settings.avatar.updated')
    broadcast_updates_pending(sln_settings)


@returns(NoneType)
@arguments(service_user=users.User, tmp_logo_key=unicode,
           x1=(float, int), y1=(float, int), x2=(float, int), y2=(float, int))
def set_logo(service_user, tmp_logo_key, x1, y1, x2, y2):
    logging.info("%s: Saving logo" % service_user.email())
    branding_settings = SolutionBrandingSettings.get(SolutionBrandingSettings.create_key(service_user))
    background_color = branding_settings.background_color if branding_settings else u'000000'
    jpg_bytes = _temp_blob_to_bytes(tmp_logo_key, x1, y1, x2, y2, SLN_LOGO_WIDTH, SLN_LOGO_HEIGHT, SLN_LOGO_MAX_SIZE,
                                    background_color)

    def trans():
        logo = get_solution_logo(service_user) or SolutionLogo(key=SolutionLogo.create_key(service_user))
        logo.picture = db.Blob(jpg_bytes)

        settings = get_solution_settings(service_user)
        settings.updates_pending = True

        put_and_invalidate_cache(logo, settings)

        deferred.defer(_regenerate_branding_with_logo, service_user, _transactional=True)

        return settings

    xg_on = db.create_transaction_options(xg=True)
    common_settings = db.run_in_transaction_options(xg_on, trans)
    send_message(common_settings.service_user, 'solutions.common.settings.logo.updated')
    broadcast_updates_pending(common_settings)


def _regenerate_branding_with_logo(service_user):
    users.set_user(service_user)
    logging.info("%s: Replacing logo.png in the sln main branding zip with the uploaded logo" % service_user.email())

    logo = get_solution_logo(service_user)
    sln_main_branding = get_solution_main_branding(service_user)

    zip_content = replace_file_in_zip_blob(sln_main_branding.blob, "logo.jpg", str(logo.picture))

    def trans():
        sln_main_branding = get_solution_main_branding(service_user)
        sln_main_branding.blob = db.Blob(zip_content)
        sln_main_branding.branding_creation_time = 0

        common_settings = get_solution_settings(service_user)
        common_settings.updates_pending = True
        common_settings.events_branding_hash = None

        put_and_invalidate_cache(sln_main_branding, common_settings)
        return common_settings

    xg_on = db.create_transaction_options(xg=True)
    common_settings = db.run_in_transaction_options(xg_on, trans)
    broadcast_updates_pending(common_settings)
