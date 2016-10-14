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
import io
import json
import logging
import os
from types import NoneType
import urllib
from zipfile import ZipFile, BadZipfile

from google.appengine.api import urlfetch
from google.appengine.ext import db
from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments, serialize_complex_value, parse_complex_value
from rogerthat.bizz.app import validate_user_regex, AppAlreadyExistsException, get_app, add_auto_connected_services
from rogerthat.bizz.branding import BrandingValidationException, store_branding_zip
from rogerthat.bizz.job import run_job, hookup_with_default_services
from rogerthat.bizz.qrtemplate import store_template
from rogerthat.bizz.rtemail import EMAIL_REGEX
from rogerthat.bizz.service import create_qr_template_key_name
from rogerthat.consts import DEBUG
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.app import get_default_app_key
from rogerthat.dal.profile import get_profile_key, get_user_profile_keys_by_app_id
from rogerthat.dal.service import get_service_identity
from rogerthat.models import App, BeaconMajor, BeaconRegion, Branding
from rogerthat.models.properties.app import AutoConnectedService, AutoConnectedServices
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to.app import CreateAppRequestTO, FacebookRoleTO, FacebookErrorTO, FacebookAccessTokenTO, \
    FacebookAppDomainTO
from rogerthat.to.beacon import BeaconRegionTO
from rogerthat.to.qrtemplates import QRTemplateWithFileTO
from rogerthat.utils import now
from rogerthat.utils.service import add_slash_default, get_service_user_from_service_identity_user
from rogerthat.utils.transactions import run_in_xg_transaction
from solution_server_settings import get_solution_server_settings
from shop.exceptions import EmptyValueException, InvalidEmailFormatException


FACEBOOK_GRAPH_URL = u'https://graph.facebook.com/v2.5/'

def validate_app(app_id, app_name, app_type, facebook_registration_enabled, fb_app_id, facebook_secret,
                 facebook_user_access_token, contact_email_address, user_regex, qr_templates_to,
                 default_qr_template_index, demo, beta, admin_services):
    if not app_id:
        raise EmptyValueException('app_id')
    if not app_name:
        raise EmptyValueException('app_name')
    if not app_type:
        raise EmptyValueException('app_type')
    if app_type not in App.TYPE_STRINGS:
        raise BusinessException('Invalid app type.')
    if facebook_registration_enabled:
        if not fb_app_id:
            raise EmptyValueException('facebook_app_id')
        if not facebook_secret:
            raise EmptyValueException('facebook_secret')
        if not facebook_user_access_token:
            raise EmptyValueException('facebook_user_access_token')
    if contact_email_address and not EMAIL_REGEX.match(contact_email_address):
        raise InvalidEmailFormatException(contact_email_address)
    if not qr_templates_to:
        raise EmptyValueException('qr_templates')
    if not default_qr_template_index and not default_qr_template_index == 0:
        raise EmptyValueException('default_qr_template_index')
    if demo is None:
        raise EmptyValueException('demo')
    if beta is None:
        raise EmptyValueException('beta')
    if user_regex:
        validate_user_regex(user_regex)

    if admin_services:
        admin_profiles = db.get([get_profile_key(u) for u in map(users.User, admin_services)])
        non_existing = list()
        for admin_email, admin_profile in zip(admin_services, admin_profiles):
            if not admin_profile:
                non_existing.append(admin_email)
        if non_existing:
            raise BusinessException('Non existing admin profiles specified: %s' % ",".join(non_existing))


@returns(App)
@arguments(app_request=CreateAppRequestTO)
def create_app_from_bob(app_request):
    android_app_id = u'com.mobicage.rogerthat.%s' % app_request.app_id.replace('-', '.')
    if app_request.app_type not in [App.APP_TYPE_CITY_APP, App.APP_TYPE_ENTERPRISE, App.APP_TYPE_YSAAA]:
        raise BusinessException(u'You may only create City, Your service as an app, or Enterprise apps.')
    if app_request.qr_template_type == 'custom':
        if not app_request.custom_qr_template:
            raise EmptyValueException('custom_qr_template')
        qr_template = app_request.custom_qr_template
        custom_qr_template_color = app_request.custom_qr_template_color
    elif app_request.qr_template_type == 'rogerthat':
        with open(os.path.join(os.path.dirname(__file__), '..', 'rogerthat', 'bizz', 'qr-brand.png')) as qr_image:
            qr_template = base64.b64encode(qr_image.read())
        custom_qr_template_color = u'363635'
    elif app_request.qr_template_type == 'oca':
        with open(os.path.dirname(__file__) + '/qr-brand-oca.png') as qr_image:
            qr_template = base64.b64encode(qr_image.read())
        custom_qr_template_color = u'5BC4BF'
    else:
        raise BusinessException(u'Invalid QR template type')
    qr_templates_to = QRTemplateWithFileTO.create(u'Default %s QR template' % app_request.app_name,
                                                  custom_qr_template_color, qr_template)
    return create_app(
        app_id=app_request.app_id,
        app_name=app_request.app_name,
        app_type=app_request.app_type,
        facebook_registration_enabled=app_request.facebook_registration_enabled,
        facebook_app_id=app_request.facebook_app_id,
        facebook_secret=app_request.facebook_secret,
        facebook_user_access_token=app_request.facebook_user_access_token,
        ios_app_id=None,
        android_app_id=android_app_id,
        dashboard_email_address=app_request.dashboard_email_address,
        contact_email_address=None,
        user_regex='',
        core_branding=app_request.core_branding,
        qr_templates_to=[qr_templates_to],
        default_qr_template_index=0,
        auto_connected_services=app_request.auto_connected_services,
        demo=False,
        beta=False,
        mdp_client_id=None,
        mdp_client_secret=None,
        orderable_apps=app_request.orderable_apps,
        admin_services=None,
        beacon_regions_to=app_request.beacon_regions_to
    )


@returns(App)
@arguments(app_id=unicode, app_name=unicode, app_type=(int, long), facebook_registration_enabled=bool,
           facebook_app_id=(int, long, NoneType), facebook_secret=unicode, facebook_user_access_token=unicode,
           ios_app_id=unicode, android_app_id=unicode, dashboard_email_address=unicode, contact_email_address=unicode,
           user_regex=unicode, core_branding=unicode, qr_templates_to=[QRTemplateWithFileTO],
           default_qr_template_index=(int, long), auto_connected_services=[AutoConnectedService], demo=bool, beta=bool,
           mdp_client_id=unicode, mdp_client_secret=unicode, orderable_apps=[unicode], admin_services=[unicode],
           beacon_regions_to=[BeaconRegionTO])
def create_app(app_id, app_name, app_type, facebook_registration_enabled, facebook_app_id, facebook_secret,
               facebook_user_access_token, ios_app_id, android_app_id, dashboard_email_address, contact_email_address,
               user_regex, core_branding, qr_templates_to, default_qr_template_index, auto_connected_services, demo,
               beta, mdp_client_id, mdp_client_secret, orderable_apps, admin_services, beacon_regions_to):
    validate_app(app_id, app_name, app_type, facebook_registration_enabled, facebook_app_id, facebook_secret,
                 facebook_user_access_token, contact_email_address, user_regex, qr_templates_to,
                 default_qr_template_index, demo, beta, admin_services)
    if facebook_registration_enabled:
        
        solution_server_settings = get_solution_server_settings()
        for user_id in solution_server_settings.bob_facebook_role_ids:
            role = FacebookRoleTO.create(user_id, FacebookRoleTO.ROLE_ADMINISTRATOR)
            try:
                set_facebook_user_role_in_app(facebook_app_id, facebook_user_access_token, role)
            except BusinessException, exception:
                logging.warn(exception)
    # Rest of the metadata is set using selenium on bob

    def trans():
        to_put = list()
        now_ = now()
        app_key = App.create_key(app_id)
        if App.get(app_key):
            raise AppAlreadyExistsException(app_id)
        app = App(key=app_key)
        app.name = app_name
        app.type = app_type
        app.facebook_registration_enabled = facebook_registration_enabled
        if facebook_registration_enabled:
            app.facebook_app_id = facebook_app_id
            app.facebook_app_secret = facebook_secret
        app.ios_app_id = ios_app_id
        app.android_app_id = android_app_id
        app.dashboard_email_address = dashboard_email_address
        app.contact_email_address = contact_email_address
        app.user_regex = user_regex
        app.creation_time = now_
        app.is_default = get_default_app_key() is None
        app.demo = demo
        app.beta = beta
        app.mdp_client_id = mdp_client_id or None
        app.mdp_client_secret = mdp_client_secret or None
        app.admin_services = admin_services or list()
        app.beacon_major = BeaconMajor.next()
        app.beacon_last_minor = 0
        for beacon_region_to in beacon_regions_to:
            assert isinstance(beacon_region_to, BeaconRegionTO)
            uuid = beacon_region_to.uuid.lower()
            major = beacon_region_to.major if beacon_region_to.has_major else None
            minor = beacon_region_to.minor if beacon_region_to.has_minor else None
            beacon_region = BeaconRegion(key=BeaconRegion.create_key(app.key(), uuid, major, minor))
            beacon_region.uuid = uuid
            beacon_region.major = major
            beacon_region.minor = minor
            beacon_region.creation_time = now_
            to_put.append(beacon_region)

        if core_branding:
            zip_stream = core_branding.decode('base64')
            try:
                zip_ = ZipFile(io.BytesIO(zip_stream))
            except BadZipfile, e:
                raise BrandingValidationException(e.message)
            branding = store_branding_zip(None, zip_, u"Core branding of %s" % app_id)
            app.core_branding_hash = branding.hash
        else:
            app.core_branding_hash = None

        app.qrtemplate_keys = list()
        for i, qr_template_to in enumerate(qr_templates_to):
            qr_image = base64.b64decode(qr_template_to.template)
            qr_template_key_name = create_qr_template_key_name(app_id, qr_template_to.description)
            store_template(None, qr_image, qr_template_to.description, qr_template_to.color, qr_template_key_name)
            if default_qr_template_index == i:
                app.qrtemplate_keys.insert(0, qr_template_key_name)
            else:
                app.qrtemplate_keys.append(qr_template_key_name)

        app.auto_connected_services = AutoConnectedServices()
        for acs in auto_connected_services:
            service_identity_user = add_slash_default(users.User(acs.service_identity_email))
            si = get_service_identity(service_identity_user)
            if not si:
                raise BusinessException("ServiceIdentity %s not found" % service_identity_user)
            acs.service_identity_email = service_identity_user.email()
            if app_id not in si.appIds:
                si.appIds.append(app_id)
                to_put.append(si)
            app.auto_connected_services.add(acs)

        app.orderable_app_ids = list(orderable_apps)
        apps = db.get(map(App.create_key, app.orderable_app_ids))
        for a in apps:
            a.orderable_app_ids.append(app_id)
            to_put.append(a)
        to_put.append(app)
        put_and_invalidate_cache(*to_put)
        connect_autoconnected_services(app_id, auto_connected_services)
        return app

    return run_in_xg_transaction(trans)


@returns()
@arguments(app_id=unicode, auto_connected_services=[AutoConnectedService])
def connect_autoconnected_services(app_id, auto_connected_services):
    for acs in auto_connected_services:
        logging.info("There is a new auto-connected service for app %s: %s", app_id, acs.service_identity_email)
        run_job(get_user_profile_keys_by_app_id, [app_id], hookup_with_default_services.run_for_auto_connected_service,
                [acs, None])


@returns(bool)
@arguments(facebook_app_id=(int, long), facebook_user_access_token=unicode, facebook_role=FacebookRoleTO)
def set_facebook_user_role_in_app(facebook_app_id, facebook_user_access_token, facebook_role):
    # Grant access to the developers.
    url = FACEBOOK_GRAPH_URL + '%d/roles?access_token=%s' % (facebook_app_id, facebook_user_access_token)
    try:
        encoded_data = urllib.urlencode(serialize_complex_value(facebook_role, FacebookRoleTO, False))
        logging.debug('Sending "publish user role" request to Facebook')
        logging.debug(encoded_data)
        result = json.loads(urlfetch.fetch(url, encoded_data, urlfetch.POST, deadline=15).content)
        logging.debug(result)
        if 'success' in result:
            return True
        else:
            error = parse_complex_value(FacebookErrorTO, result, False)
            error_message = parse_facebook_error(error)
            if error.error.error_user_title is not MISSING and 'You cannot change your own role' in error_message:
                logging.info('Not raising error: %s', error_message)
                return True
            else:
                raise BusinessException(error_message)
    except urlfetch.DownloadError, exception:
        msg = 'Failed to update Facebook user role (%s)' % exception.message
        logging.exception(msg)
        raise BusinessException(msg)


@returns(unicode)
@arguments(facebook_app_id=(int, long), facebook_app_secret=unicode, from_server=bool)
def get_facebook_access_token(facebook_app_id, facebook_app_secret, from_server=False):
    if not from_server:
        # this works as well as access token and doesn't require an additional request
        return '%s|%s' % (facebook_app_id, facebook_app_secret)
    try:
        logging.debug('Fetching Facebook access token for facebook app %s' % facebook_app_id)
        url = FACEBOOK_GRAPH_URL + 'oauth/access_token?client_id=%d&client_secret=%s&grant_type=client_credentials' % (
            facebook_app_id, facebook_app_secret)
        result = urlfetch.fetch(url, deadline=15)
        facebook_access_token = parse_complex_value(FacebookAccessTokenTO, json.loads(result.content), False)
        logging.debug(facebook_access_token)
        if facebook_access_token.error is not MISSING:
            error_message = parse_facebook_error(facebook_access_token)
            raise BusinessException(error_message)
        return facebook_access_token.access_token
    except urlfetch.DownloadError, exception:
        msg = 'Failed to get Facebook access token (%s)' % exception.message
        logging.exception(msg)
        raise BusinessException(msg)


@returns(bool)
@arguments(facebook_app_id=(int, long), facebook_app_secret=unicode, app_domain=FacebookAppDomainTO)
def set_facebook_app_domain(facebook_app_id, facebook_app_secret, app_domain):
    access_token = get_facebook_access_token(facebook_app_id, facebook_app_secret)
    url = FACEBOOK_GRAPH_URL + '%d?access_token=%s' % (facebook_app_id, access_token)
    try:
        encoded_data = urllib.urlencode(serialize_complex_value(app_domain, FacebookAppDomainTO, False))
        logging.debug('Sending "update app info" (to set app domain) request to Facebook')
        logging.debug(encoded_data)
        result = json.loads(urlfetch.fetch(url, encoded_data, urlfetch.POST, deadline=15).content)
        logging.debug(result)
        if 'success' in result:
            return True
        else:
            error = parse_complex_value(FacebookErrorTO, result, False)
            error_message = parse_facebook_error(error)
            raise BusinessException(error_message)
    except urlfetch.DownloadError, exception:
        msg = 'Failed to set Facebook app domain (%s)' % exception.message
        logging.exception(msg)
        raise BusinessException(msg)


@returns(unicode)
@arguments(error=FacebookErrorTO)
def parse_facebook_error(error):
    msg = u'Facebook returned: '
    if error.error.error_user_title is not MISSING:
        return msg + error.error.error_user_title
    if error.error.error_user_msg is not MISSING:
        return msg + error.error.error_user_msg
    if error.error.message is not MISSING:
        return msg + error.error.message


@returns(unicode)
@arguments(app_id=unicode, main_service_email=unicode)
def validate_and_put_main_service(app_id, main_service_email):
    app = get_app(app_id)
    service_identity_user = add_slash_default(users.User(main_service_email))
    service_identity = get_service_identity(service_identity_user)
    if not service_identity:
        raise BusinessException('Cannot set main service, invalid service email.')

    already_has_service = False
    for acs in app.auto_connected_services:
        if acs.service_identity_email == service_identity_user.email():
            already_has_service = True
            break
    if not already_has_service:
        auto_connected_service = AutoConnectedService.create(main_service_email, False, None, None)
        add_auto_connected_services(app_id, [auto_connected_service])
    message = None
    if not app.core_branding_hash:
        service_user = get_service_user_from_service_identity_user(service_identity_user)
        brandings = sorted(Branding.list_by_user(service_user), key=lambda b: b.timestamp, reverse=True)
        branding_to_copy = None
        for branding in brandings:
            if branding.description == 'Main':
                branding_to_copy = branding
                break
        if branding_to_copy:
            def trans():
                app = get_app(app_id)
                app.core_branding_hash = branding_to_copy.hash
                app.put()

            db.run_in_transaction(trans)
        else:
            message = "Could not find main branding for app %s. Did not set core branding." % app.name
    return message


@returns()
@arguments(app_id=unicode, playstore_track=unicode)
def put_app_track(app_id, playstore_track):
    app = get_app(app_id)
    app.beta = playstore_track != 'production'
    app.put()
