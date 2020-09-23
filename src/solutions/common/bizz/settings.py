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
import logging
from urlparse import urlparse

from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred, ndb

from mcfw.consts import MISSING
from mcfw.exceptions import HttpNotFoundException
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.service import _validate_service_identity
from rogerthat.consts import FAST_QUEUE
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.app import get_apps_by_id
from rogerthat.models import ServiceIdentity
from rogerthat.models.maps import MapServiceMediaItem
from rogerthat.models.news import MediaType
from rogerthat.models.settings import SyncedNameValue, ServiceAddress, SyncedField, ServiceInfo
from rogerthat.rpc import users
from rogerthat.service.api.system import put_avatar
from rogerthat.to.news import BaseMediaTO
from rogerthat.to.service import ServiceIdentityDetailsTO
from rogerthat.utils import now
from rogerthat.utils.channel import send_message
from rogerthat.utils.cloud_tasks import schedule_tasks, create_task
from rogerthat.utils.transactions import run_in_transaction
from rogerthat.utils.zip_utils import replace_file_in_zip_blob
from solutions import translate
from solutions.common.bizz import broadcast_updates_pending, SolutionModule
from solutions.common.cron.news.rss import parse_rss_items
from solutions.common.dal import get_solution_settings, get_solution_main_branding, \
    get_solution_settings_or_identity_settings
from solutions.common.exceptions.settings import InvalidRssLinksException
from solutions.common.models import SolutionSettings, \
    SolutionBrandingSettings, SolutionRssScraperSettings, SolutionRssLink, SolutionMainBranding, \
    SolutionServiceConsent
from solutions.common.to import SolutionSettingsTO
from solutions.common.to.settings import ServiceInfoTO, PrivacySettingsTO, PrivacySettingsGroupTO
from solutions.common.utils import is_default_service_identity, send_client_action


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
        _validate_service_identity(to)


@returns(tuple)
@arguments(service_user=users.User, service_identity=unicode, data=SolutionSettingsTO)
def save_settings(service_user, service_identity, data):
    # type: (users.User, unicode, SolutionSettingsTO) -> Tuple[SolutionSettings, SolutionIdentitySettings]
    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)

    if data.events_visible is not None:
        sln_settings.events_visible = data.events_visible

    if data.inbox_email_reminders is not None:
        sln_i_settings.inbox_email_reminders_enabled = data.inbox_email_reminders

    if data.iban is not MISSING:
        sln_settings.iban = data.iban
    if data.bic is not MISSING:
        sln_settings.bic = data.bic

    sln_settings.updates_pending = True
    validate_sln_settings(sln_settings)
    if not is_default_service_identity(service_identity):
        sln_i_settings.put()
    sln_settings.put()
    broadcast_updates_pending(sln_settings)

    return sln_settings, sln_i_settings


@returns(SolutionBrandingSettings)
@arguments(service_user=users.User, image_url=unicode)
def set_avatar(service_user, image_url):
    result = urlfetch.fetch(image_url)  # type: urlfetch._URLFetchResult
    jpg_bytes = result.content

    def trans():
        keys = SolutionBrandingSettings.create_key(service_user), SolutionSettings.create_key(service_user)
        branding_settings, sln_settings = db.get(keys)  # type: SolutionBrandingSettings, SolutionSettings

        if branding_settings.avatar_url == image_url:
            return sln_settings, branding_settings

        sln_settings.updates_pending = True
        branding_settings.avatar_url = image_url
        branding_settings.modification_time = now()

        put_and_invalidate_cache(sln_settings, branding_settings)
        put_avatar(base64.b64encode(jpg_bytes))

        return sln_settings, branding_settings

    sln_settings, branding_settings = run_in_transaction(trans, xg=True)
    send_message(sln_settings.service_user, 'solutions.common.settings.avatar.updated', avatar_url=image_url)
    broadcast_updates_pending(sln_settings)
    return branding_settings


@returns(SolutionBrandingSettings)
@arguments(service_user=users.User, image_url=unicode, service_identity=unicode)
def set_logo(service_user, image_url, service_identity):
    branding_settings = db.get(SolutionBrandingSettings.create_key(service_user))  # type: SolutionBrandingSettings
    if image_url == branding_settings.logo_url:
        return branding_settings
    branding_settings.logo_url = image_url
    branding_settings.modification_time = now()
    branding_settings.put()

    tasks = [
        create_task(save_logo_to_media, service_user, service_identity, branding_settings.logo_url),
        create_task(_regenerate_branding_with_logo, service_user),
    ]
    schedule_tasks(tasks, FAST_QUEUE)
    return branding_settings


def save_logo_to_media(service_user, service_identity, logo_url):
    service_info, changed = _save_logo_to_media(service_user, service_identity, logo_url)
    if changed:
        send_client_action(service_user, {'type': '[settings] Update service info complete',
                                          'payload': ServiceInfoTO.from_model(service_info).to_dict()})


@ndb.transactional()
def _save_logo_to_media(service_user, service_identity, logo_url):
    # type: (users.User, str, str) -> Tuple[ServiceInfo, bool]
    service_info = get_service_info(service_user, service_identity)
    for media in service_info.cover_media:
        if media.item.content == logo_url:
            # Already present in cover media list, don't do anything
            return service_info, False
    media_item = MapServiceMediaItem()
    media_item.item = BaseMediaTO()
    media_item.item.type = MediaType.IMAGE
    media_item.item.content = logo_url
    service_info.cover_media.insert(0, media_item)
    service_info.put()
    return service_info, True


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
    send_message(service_user, 'solutions.common.settings.logo.updated', logo_url=branding_settings.logo_url)


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


@ndb.non_transactional()
def _get_lang(service_user):
    return get_solution_settings(service_user).main_language


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
        raise InvalidRssLinksException(invalid_urls, _get_lang(service_user))

    rss_settings.notify = data.notify
    scraper_urls = []
    rss_links = []
    for scraper in reversed(data.scrapers):
        if scraper.url in scraper_urls:
            continue
        scraper_urls.append(scraper.url)
        rss_links.append(SolutionRssLink(url=scraper.url,
                                         dry_runned=current_dict.get(scraper.url, False),
                                         group_type=scraper.group_type if scraper.group_type else None,
                                         community_ids=scraper.community_ids))
    rss_settings.rss_links = [rss_link for rss_link in reversed(rss_links)]
    rss_settings.put()
    return rss_settings


def get_service_info(service_user, service_identity):
    # type: (users.User, str) -> ServiceInfo
    if not service_identity:
        service_identity = ServiceIdentity.DEFAULT
    return ServiceInfo.create_key(service_user, service_identity).get()


def update_service_info(service_user, service_identity, data):
    # type: (users.User, str, ServiceInfoTO) -> ServiceInfo
    service_info = get_service_info(service_user, service_identity)
    service_info_dict = service_info.to_dict()
    service_info.addresses = [ServiceAddress.from_to(a) for a in data.addresses]
    service_info.cover_media = [MapServiceMediaItem.from_to(m) for m in data.cover_media]
    service_info.currency = data.currency
    service_info.description = data.description
    service_info.email_addresses = [SyncedNameValue.from_to(v) for v in data.email_addresses]
    service_info.keywords = data.keywords
    service_info.name = data.name
    service_info.phone_numbers = [SyncedNameValue.from_to(v) for v in data.phone_numbers]
    service_info.main_place_type = data.main_place_type
    service_info.place_types = data.place_types
    service_info.synced_fields = [SyncedField.from_to(v) for v in data.synced_fields]
    service_info.timezone = data.timezone
    service_info.visible = data.visible
    service_info.websites = [SyncedNameValue.from_to(v) for v in data.websites]
    if service_info_dict != service_info.to_dict():
        sln_settings = get_solution_settings(service_user)
        service_info.visible = service_info.visible and sln_settings.hidden_by_city is None
        service_info.put()
        sln_settings.updates_pending = True
        # Temporarily copying these properties until we have cleaned up all usages of them
        # TODO: remove properties from SolutionSettings
        sln_settings.timezone = service_info.timezone
        sln_settings.phone_number = service_info.main_phone_number
        sln_settings.address = service_info.main_address(sln_settings.locale)
        sln_settings.currency = service_info.currency
        sln_settings.name = service_info.name
        sln_settings.put()
        deferred.defer(broadcast_updates_pending, sln_settings)
    return service_info


def validate_url(url, check_existence=True):
    url = url.strip() \
        .lower() \
        .replace('W.W.W.,', 'www.') \
        .replace('www,', 'www.')
    if not url:
        return None
    if url.startswith('www.'):
        # We can't assume https here
        url = 'http://%s' % url
    if not url.startswith('http'):
        url = 'http://%s' % url
    if '.' not in url:
        return None
    if check_existence:
        return resolve_url(url)
    return url


def resolve_url(url):
    try:
        result = urlfetch.fetch(url, urlfetch.HEAD, follow_redirects=False,
                                deadline=5)  # type: urlfetch._URLFetchResult
        if result.status_code == 200:
            return url
        elif result.status_code in (301, 302):
            return result.headers['location']
    except Exception as e:
        logging.debug('Error while checking url %s: %s', url, e.message, exc_info=True)
    return None


def parse_facebook_url(url):
    try:
        # type: (str) -> Optional[str]
        page = url.strip() \
            .replace('m.facebook', 'facebook') \
            .replace('fb.com', 'facebook.com') \
            .replace('nl-nl.', '') \
            .replace('http:', 'https:')
        if page.startswith('@'):
            page = 'https://www.facebook.com/%s' % page.strip('@')
        elif not page.lower().startswith('https'):
            page = 'https://%s' % page
        parsed = validate_url(page, check_existence=False)
        if not parsed:
            return None
        result = urlparse(page)  # type: ParseResult
        netloc = result.netloc.lower()
        if not netloc.startswith('business') and not netloc.startswith('www.'):
            netloc = 'www.%s' % netloc
        if netloc in ('business.facebook.com', 'www.facebook.com'):
            page_url = 'https://{netloc}{path}'.format(netloc=netloc, path=result.path)
            if 'id=' in result.query or 'q=' in result.query:
                return page_url + '?%s' % result.query
            return page_url
    except:
        logging.debug('parse_facebook_url invalid_url: %s', url, exc_info=True)
    return None


def get_cirklo_privacy_groups(lang):
    from markdown import Markdown
    from solutions.common.markdown_newtab import NewTabExtension
    groups = [
        PrivacySettingsGroupTO(
            page=1,
            description='<h4>%s</h4>' % translate(lang, 'consent_share_with_city'),
            items=[PrivacySettingsTO(
                type=SolutionServiceConsent.TYPE_CITY_CONTACT,
                enabled=False,
                label=translate(lang, 'consent_city_contact')
            )]
        )
    ]
    md = Markdown(output='html', extensions=['nl2br', NewTabExtension()])
    lines = [
        '#### %s' % translate(lang, 'cirklo_info_title'),
        translate(lang, 'cirklo_info_text'),
        '',
        translate(lang, 'cirklo_participation_text'),
    ]
    groups.append(PrivacySettingsGroupTO(
        page=2,
        description=md.convert('\n\n'.join(lines)),
        items=[PrivacySettingsTO(
            type=SolutionServiceConsent.TYPE_CIRKLO_SHARE,
            enabled=False,
            label=translate(lang, 'consent_cirklo_share')
        )]))
    return groups


def get_consents_for_community(community_id, lang, user_consent_types):
    from markdown import Markdown
    from solutions.common.markdown_newtab import NewTabExtension
    community = get_community(community_id)
    if not community:
        raise HttpNotFoundException('Community %s not found' % community_id)
    service_user = users.User(community.main_service)
    city_service_settings = get_solution_settings(service_user)
    groups = [
        PrivacySettingsGroupTO(
            page=1,
            description='<h4>%s</h4>' % translate(lang, 'consent_share_with_city'),
            items=[PrivacySettingsTO(
                type=SolutionServiceConsent.TYPE_CITY_CONTACT,
                enabled=SolutionServiceConsent.TYPE_CITY_CONTACT in user_consent_types,
                label=translate(lang, 'consent_city_contact')
            )]
        ),
        PrivacySettingsGroupTO(
            page=1,
            description='<h4>%s</h4>' % translate(lang, 'consent_platform_communication'),
            items=[
                PrivacySettingsTO(
                    type=SolutionServiceConsent.TYPE_NEWSLETTER,
                    enabled=SolutionServiceConsent.TYPE_NEWSLETTER in user_consent_types,
                    label=translate(lang, 'email_consent_newsletter')
                ), PrivacySettingsTO(
                    type=SolutionServiceConsent.TYPE_EMAIL_MARKETING,
                    enabled=SolutionServiceConsent.TYPE_EMAIL_MARKETING in user_consent_types,
                    label=translate(lang, 'email_consent_marketing')
                )
            ]
        )
    ]
    md = Markdown(output='html', extensions=['nl2br', NewTabExtension()])
    if SolutionModule.CIRKLO_VOUCHERS in city_service_settings.modules:
        lines = [
            '#### %s' % translate(lang, 'cirklo_info_title'),
            translate(lang, 'cirklo_info_text'),
            '',
            translate(lang, 'cirklo_participation_text'),
        ]
        groups.append(PrivacySettingsGroupTO(
            page=2,
            description=md.convert('\n\n'.join(lines)),
            items=[PrivacySettingsTO(
                type=SolutionServiceConsent.TYPE_CIRKLO_SHARE,
                enabled=SolutionServiceConsent.TYPE_CIRKLO_SHARE in user_consent_types,
                label=translate(lang, 'consent_cirklo_share')
            )]))
    return groups
