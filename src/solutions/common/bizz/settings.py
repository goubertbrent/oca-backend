# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

import base64
from cStringIO import StringIO
import cgi
import logging
from types import NoneType
from xml.dom import minidom

from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred, ndb

from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments
from rogerthat.bizz.opening_hours import save_textual_opening_hours
from rogerthat.bizz.service import _validate_service_identity
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.rpc import users
from rogerthat.service.api.system import put_avatar
from rogerthat.to.service import ServiceIdentityDetailsTO
from rogerthat.utils import now
from rogerthat.utils.channel import send_message
from rogerthat.utils.transactions import run_in_transaction
from rogerthat.utils.zip_utils import replace_file_in_zip_blob
from solutions.common.bizz import _get_location, broadcast_updates_pending
from solutions.common.bizz.images import upload_file
from solutions.common.cron.news.rss import parse_rss_items
from solutions.common.dal import get_solution_settings, get_solution_main_branding, \
    get_solution_settings_or_identity_settings
from solutions.common.exceptions.settings import InvalidRssLinksException
from solutions.common.models import SolutionSettings, \
    SolutionBrandingSettings, SolutionRssScraperSettings, SolutionRssLink, SolutionMainBranding
from solutions.common.to import SolutionSettingsTO
from solutions.common.utils import is_default_service_identity


SLN_LOGO_WIDTH = 640
SLN_LOGO_HEIGHT = 240
SLN_LOGO_MAX_SIZE = 102400  # 100 kB
SLN_AVATAR_WIDTH = 150
SLN_AVATAR_HEIGHT = 150
SLN_AVATAR_MAX_SIZE = 51200  # 50 kB


def validate_sln_settings(sln_settings):
    # type: (SolutionSettings) -> None
    for identity in sln_settings.identities:
        to = ServiceIdentityDetailsTO(identifier=identity, name=sln_settings.name)
        _validate_service_identity(to, False)


@returns(tuple)
@arguments(service_user=users.User, service_identity=unicode, data=SolutionSettingsTO)
def save_settings(service_user, service_identity, data):
    # type: (users.User, unicode, SolutionSettingsTO) -> tuple[SolutionSettings, SolutionIdentitySettings]
    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
    sln_i_settings.name = data.name
    sln_i_settings.description = data.description
    sln_i_settings.opening_hours = data.opening_hours
    deferred.defer(save_textual_opening_hours, service_user.email() if is_default_service_identity(service_identity) else sln_i_settings.service_identity_user.email(), sln_settings.opening_hours)
    sln_i_settings.phone_number = data.phone_number

    if data.email_address and data.email_address != service_user.email():
        sln_i_settings.qualified_identifier = data.email_address
    else:
        sln_i_settings.qualified_identifier = None

    if data.currency is not None:
        sln_settings.currency = data.currency
    sln_settings.search_enabled = data.search_enabled
    sln_settings.search_enabled_check = data.search_enabled_check

    sln_i_settings.search_keywords = data.search_keywords
    if data.address and (sln_i_settings.address != data.address or not sln_i_settings.location):
        sln_i_settings.address = data.address
        try:
            lat, lon = _get_location(data.address)
            sln_i_settings.location = db.GeoPt(lat, lon)
        except:
            logging.warning('Failed to resolve address: %s' % sln_i_settings.address, exc_info=1)
            sln_i_settings.location = None
    if data.timezone is not None:
        if sln_settings.timezone != data.timezone:
            send_message(service_user, u"solutions.common.settings.timezoneChanged")
        sln_settings.timezone = data.timezone

    if data.events_visible is not None:
        sln_settings.events_visible = data.events_visible

    if data.inbox_email_reminders is not None:
        sln_i_settings.inbox_email_reminders_enabled = data.inbox_email_reminders

    if data.iban is not MISSING:
        sln_settings.iban = data.iban
    if data.bic is not MISSING:
        sln_settings.bic = data.bic
        
    if data.place_types is not MISSING:
        sln_i_settings.place_types = data.place_types

    sln_settings.updates_pending = True
    validate_sln_settings(sln_settings)
    if not is_default_service_identity(service_identity):
        sln_i_settings.put()
    sln_settings.put()
    broadcast_updates_pending(sln_settings)

    return sln_settings, sln_i_settings


@returns(SolutionBrandingSettings)
@arguments(service_user=users.User, image=unicode)
def set_avatar(service_user, image):
    _meta, img_b64 = image.split(',')
    jpg_bytes = base64.b64decode(img_b64)
    content_type = _meta.lstrip('data:').split(';')[0]
    file_ = cgi.FieldStorage(StringIO(jpg_bytes), {'content-type': content_type})
    branding_settings_key = SolutionBrandingSettings.create_key(service_user)
    reference = ndb.Key.from_old_key(branding_settings_key)  # @UndefinedVariable
    uploaded_file = upload_file(service_user, file_, 'branding/avatar', reference)

    def trans():
        branding_settings, sln_settings = db.get((branding_settings_key,
                                                  SolutionSettings.create_key(service_user)))
        sln_settings.updates_pending = True
        branding_settings.avatar_url = uploaded_file.url
        branding_settings.modification_time = now()

        put_and_invalidate_cache(sln_settings, branding_settings)
        put_avatar(img_b64)

        return sln_settings, branding_settings

    sln_settings, branding_settings = run_in_transaction(trans, xg=True)
    send_message(sln_settings.service_user, 'solutions.common.settings.avatar.updated')
    broadcast_updates_pending(sln_settings)
    return branding_settings


@returns(SolutionBrandingSettings)
@arguments(service_user=users.User, image=unicode)
def set_logo(service_user, image):
    _meta, img_b64 = image.split(',')
    jpg_bytes = base64.b64decode(img_b64)
    content_type = _meta.lstrip('data:').split(';')[0]
    file_ = cgi.FieldStorage(StringIO(jpg_bytes), {'content-type': content_type})
    branding_settings_key = SolutionBrandingSettings.create_key(service_user)
    reference = ndb.Key.from_old_key(branding_settings_key)  # @UndefinedVariable
    uploaded_file = upload_file(service_user, file_, 'branding/logo', reference)

    branding_settings = db.get(branding_settings_key)  # type: SolutionBrandingSettings
    branding_settings.logo_url = uploaded_file.url
    branding_settings.modification_time = now()
    branding_settings.put()

    deferred.defer(_regenerate_branding_with_logo, service_user)
    return branding_settings


def _regenerate_branding_with_logo(service_user):
    users.set_user(service_user)
    logging.info("%s: Replacing logo.png in the sln main branding zip with the uploaded logo" % service_user.email())
    sln_main_branding, branding_settings = db.get((SolutionMainBranding.create_key(service_user),
                                                   SolutionBrandingSettings.create_key(service_user)))
    picture = branding_settings.download_logo()
    zip_content = replace_file_in_zip_blob(sln_main_branding.blob, 'logo.jpg', str(picture))

    def trans():
        sln_main_branding = get_solution_main_branding(service_user)
        sln_main_branding.blob = db.Blob(zip_content)
        sln_main_branding.branding_creation_time = 0

        common_settings = get_solution_settings(service_user)
        common_settings.updates_pending = True

        put_and_invalidate_cache(sln_main_branding, common_settings)
        return common_settings

    common_settings = run_in_transaction(trans, xg=True)
    broadcast_updates_pending(common_settings)


def _validate_rss_urls(urls):
    # type: (set[str]) -> tuple[list[str], list[str]]
    rpcs = []
    invalid_urls = []
    valid_urls = []
    for rss_url in urls:
        rpc = urlfetch.create_rpc(deadline=30)
        try:
            urlfetch.make_fetch_call(rpc, rss_url)
            rpcs.append(rpc)
        except Exception as e:
            logging.debug('Error while creating fetch call for %s: %s', rss_url, e.message)
            rpcs.append(None)
    for rss_url, rpc in zip(urls, rpcs):
        if not rpc:
            invalid_urls.append(rss_url)
            continue
        try:
            response = rpc.get_result()  # type: urlfetch._URLFetchResult
        except Exception as e:
            logging.debug('Error while fetching %s: %s', rss_url, e.message)
            invalid_urls.append(rss_url)
            continue
        if response.status_code != 200:
            invalid_urls.append(rss_url)
        else:
            try:
                items, _ = parse_rss_items(response.content, rss_url)
                if not items:
                    raise Exception('Missing items %s' % rss_url)
            except Exception as e:
                logging.debug('Error while validating url: %s' % e.message, exc_info=True)
                invalid_urls.append(rss_url)
    return valid_urls, invalid_urls


@ndb.transactional()
def save_rss_urls(service_user, service_identity, data):
    # type: (users.User, unicode, SolutionRssSettingsTO) -> SolutionRssScraperSettings
    rss_settings_key = SolutionRssScraperSettings.create_key(service_user, service_identity)
    rss_settings = rss_settings_key.get()  # type: SolutionRssScraperSettings

    current_dict = {}
    if not rss_settings:
        rss_settings = SolutionRssScraperSettings(key=rss_settings_key)
    else:
        for rss_links in rss_settings.rss_links:
            if not current_dict.get(rss_links.url, False):
                current_dict[rss_links.url] = rss_links.dry_runned
    _, invalid_urls = _validate_rss_urls({scraper.url for scraper in data.scrapers if scraper.url not in current_dict})
    if invalid_urls:
        raise InvalidRssLinksException(invalid_urls)

    rss_settings.notify = data.notify
    rss_settings.rss_links = [SolutionRssLink(url=scraper.url,
                                              dry_runned=current_dict.get(scraper.url, False),
                                              group_type=scraper.group_type if scraper.group_type else None,
                                              app_ids=[app_id for app_id in scraper.app_ids if app_id]) for scraper in data.scrapers]
    rss_settings.put()
    return rss_settings
