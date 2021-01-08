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
import json
import logging
import types
import uuid
from collections import defaultdict
from random import choice

from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred

from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments, parse_complex_value
from mcfw.utils import chunks
from rogerthat.bizz.communities.communities import get_communities_by_id
from rogerthat.bizz.friends import ack_invitation_by_invitation_secret, makeFriends, ORIGIN_YSAAA, \
    REGISTRATION_ORIGIN_QR, ACCEPT_AND_CONNECT_ID, register_result_response_receiver, REGISTRATION_ORIGIN_DEFAULT, \
    REGISTRATION_ORIGIN_OAUTH, ORIGIN_USER_INVITE
from rogerthat.bizz.job import hookup_with_default_services
from rogerthat.bizz.messaging import send_messages_after_registration
from rogerthat.bizz.profile import create_user_profile
from rogerthat.bizz.roles import grant_service_roles
from rogerthat.bizz.service.mfr import start_local_flow
from rogerthat.bizz.system import update_settings_response_handler, unregister_mobile
from rogerthat.bizz.user import delete_user_data
from rogerthat.capi.system import updateSettings
from rogerthat.consts import MC_DASHBOARD, DEBUG, FAST_QUEUE
from rogerthat.dal import parent_key, put_and_invalidate_cache, parent_ndb_key
from rogerthat.dal.app import get_app_by_id, get_app_settings
from rogerthat.dal.friend import get_friends_map_key_by_user
from rogerthat.dal.mobile import get_mobile_by_account, get_user_active_mobiles, \
    get_mobile_settings_cached
from rogerthat.dal.profile import get_user_profile_key, get_user_profile, \
    get_service_profile, get_profile_key, get_profiles
from rogerthat.dal.registration import get_registration_by_mobile
from rogerthat.dal.service import get_service_identity
from rogerthat.models import InstallationLog, UserInteraction, ProfilePointer, App, ServiceIdentity, \
    InstallationStatus, Installation, UserConsentHistory, UserData, FacebookUserProfile
from rogerthat.models.properties.profiles import MobileDetails
from rogerthat.rpc import users
from rogerthat.rpc.models import Mobile
from rogerthat.rpc.rpc import logError
from rogerthat.rpc.service import logServiceError
from rogerthat.service.api.app import installation_progress_response_receiver, installation_progress
from rogerthat.settings import get_server_settings
from rogerthat.templates import JINJA_ENVIRONMENT
from rogerthat.to.friends import RegistrationResultRolesTO
from rogerthat.to.installation import InstallationLogTO, InstallationTO
from rogerthat.to.registration import AccountTO, MobileInfoTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.to.system import SettingsTO, UpdateSettingsRequestTO
from rogerthat.translations import DEFAULT_LANGUAGE, localize
from rogerthat.utils import channel, now, try_or_defer, bizz_check, is_flag_set, urlencode
from rogerthat.utils.app import create_app_user, get_app_id_from_app_user, get_human_user_from_app_user, \
    get_app_user_tuple
from rogerthat.utils.crypto import encrypt_for_jabber_cloud, decrypt_from_jabber_cloud
from rogerthat.utils.service import get_service_identity_tuple, add_slash_default, create_service_identity_user
from rogerthat.utils.transactions import run_in_xg_transaction, run_in_transaction
from rogerthat.utils.translations import localize_app_translation


@arguments(app_id=unicode)
def get_communities_by_app_id( app_id):
    # type: (unicode) -> List[dict]
    app = get_app_by_id(app_id)
    return [{'id': c.id, 'name': c.name} for c in get_communities_by_id(app.community_ids)]


def get_device_name(hardware_model, sim_carrier_name):
    if hardware_model and sim_carrier_name:
        return u"%s (%s)" % (hardware_model, sim_carrier_name)
    if hardware_model:
        return hardware_model
    return None


@returns([unicode])
@arguments(human_user=users.User, language=unicode, app_id=unicode, device_id=unicode)
def get_device_names_of_my_mobiles(human_user, language, app_id, device_id):
    device_names = []
    app_user = create_app_user(human_user, app_id)
    mobiles = get_user_active_mobiles(app_user)
    for m in mobiles:
        if device_id and m.deviceId == device_id:
            continue
        name = get_device_name(m.hardwareModel, m.simCarrierName)
        if not name:
            name = localize(language, u"Unknown")
        device_names.append(name)
    return device_names


@returns(types.TupleType)
@arguments(human_user=users.User, name=unicode, first_name=unicode, last_name=unicode, app_id=unicode, use_xmpp_kick_channel=bool,
           gcm_registration_id=unicode, language=unicode, ysaaa=bool, firebase_registration_id=unicode,
           hardware_model=unicode, sim_carrier_name=unicode, tos_version=(int, long, types.NoneType),
           consent_push_notifications_shown=bool, anonymous_account=unicode, community_id=(int, long))
def register_mobile(human_user, name=None, first_name=None, last_name=None, app_id=App.APP_ID_ROGERTHAT, use_xmpp_kick_channel=True,
                    gcm_registration_id=None, language=None, ysaaa=False, firebase_registration_id=None,
                    hardware_model=None, sim_carrier_name=None, tos_version=None,
                    consent_push_notifications_shown=False, anonymous_account=None, community_id=0):
    if anonymous_account:
        anonymous_mobile = get_mobile_by_account(anonymous_account)
        azzert(anonymous_mobile)

    app = get_app_by_id(app_id)
    if community_id == 0:
        azzert(len(app.community_ids) == 1, "Community was NOT provided but len(app.community_ids) != 1")
        community_id = app.community_ids[0]
    else:
        azzert(community_id in app.community_ids, "Community was provided but not found in app.community_ids")

    # First unregister currently registered mobiles
    app_user = create_app_user(human_user, app_id)
    mobiles = get_user_active_mobiles(app_user)

    reason = None
    device_name = get_device_name(hardware_model, sim_carrier_name)
    if device_name:
        reason = localize(language, u"Your device was unregistered because the same account was used to register the following device '%(device_name)s'",
                          device_name=device_name)

    for m in mobiles:
        unregister_mobile(app_user, m, reason)

    # Create account
    account = generate_account()

    # Save mobile in datastore
    mobile = Mobile(key_name=account.account)
    mobile.id = unicode(uuid.uuid1())
    mobile.description = "%s mobile" % app_user.email()

    mobile.user = app_user
    mobile.account = account.account
    mobile.accountPassword = account.password
    if use_xmpp_kick_channel:
        mobile.status = Mobile.STATUS_NEW  # Account created status is set as soon as the ejabberd account is ready
    else:
        mobile.status = Mobile.STATUS_NEW | Mobile.STATUS_ACCOUNT_CREATED
    if gcm_registration_id:
        mobile.pushId = gcm_registration_id
    if firebase_registration_id:
        mobile.pushId = firebase_registration_id
    mobile.put()

    if use_xmpp_kick_channel:
        try_or_defer(create_jabber_account, account, mobile.key())

    age_and_gender_set = False
    owncloud_password = unicode(uuid.uuid4()) if app.owncloud_base_uri else None

    # Create profile for user if needed
    user_profile = get_user_profile(app_user)
    if not user_profile:
        create_user_profile(app_user, name or human_user.email()[:40], language, ysaaa, owncloud_password, tos_version=tos_version,
                            consent_push_notifications_shown=consent_push_notifications_shown, first_name=first_name, last_name=last_name,
                            community_id=community_id)
        if owncloud_password:
            create_owncloud_account(
                app_user, app.owncloud_base_uri, app.owncloud_admin_username, app.owncloud_admin_password, owncloud_password)
    else:
        should_put = False
        if isinstance(user_profile, FacebookUserProfile) or user_profile.birthdate is not None and user_profile.gender is not None:
            age_and_gender_set = True
        if user_profile.isCreatedForService:
            user_profile.isCreatedForService = False
            should_put = True
        if owncloud_password and not user_profile.owncloud_password:
            user_profile.owncloud_password = owncloud_password
            should_put = True
            create_owncloud_account(
                app_user, app.owncloud_base_uri, app.owncloud_admin_username, app.owncloud_admin_password, owncloud_password)

        if tos_version:
            user_profile.tos_version = tos_version
            should_put = True

        if not user_profile.community_id or community_id != user_profile.community_id:
            user_profile.community_id = community_id
            should_put = True

        if should_put:
            user_profile.put()

    return account, mobile, age_and_gender_set


def get_headers_for_consent(request):
    if not DEBUG:
        from pprint import pformat
        logging.info("Environ: %s" % pformat(request.environ))
        for header, value in request.headers.iteritems():
            logging.info("%s: %s" % (header, value))
    header_keys = ['Host', 'Referrer', 'Origin', 'User-Agent', 'X-Appengine-Country', 'X-Appengine-Citylatlong',
                   'X-Appengine-Region', 'X-Appengine-City', 'X-Forwarded-For', 'X-Forwarded-Host']
    return {key: request.headers[key] for key in header_keys if key in request.headers}


def save_tos_consent(app_user, headers, version, age):
    data = dict(headers=headers,
                version=version,
                age=age)
    UserConsentHistory(consent_type=UserConsentHistory.TYPE_TOS,
                       data=data,
                       parent=parent_ndb_key(app_user)).put()


def save_push_notifications_consent(app_user, headers, enabled):
    data = dict(headers=headers,
                enabled=enabled)
    UserConsentHistory(consent_type=UserConsentHistory.TYPE_PUSH_NOTIFICATIONS,
                       data=data,
                       parent=parent_ndb_key(app_user)).put()


def create_owncloud_account(app_user, owncloud_base_uri, owncloud_admin_username, owncloud_admin_password, owncloud_password):
    pass
    # Owncloud is disabled for now
    #deferred.defer(_create_owncloud_account, app_user, owncloud_base_uri, owncloud_admin_username, owncloud_admin_password, owncloud_password)


def _create_owncloud_account(app_user, owncloud_base_uri, owncloud_admin_username, owncloud_admin_password, owncloud_password):
    human_user, app_id = get_app_user_tuple(app_user)
    post_args = {"userid": "%s_%s" % (human_user.email(), app_id), "password": owncloud_password}
    post_data = urlencode(post_args)

    headers = {'Authorization': 'Basic %s' %
               base64.b64encode("%s:%s" % (owncloud_admin_username, owncloud_admin_password))}

    url = "%s/ocs/v1.php/cloud/users" % owncloud_base_uri

    response = urlfetch.fetch(url, post_data, "POST", headers, deadline=55)
    logging.debug("owncloud response.status_code: %s", response.status_code)
    logging.debug("owncloud response.content: %s", response.content)


@returns()
@arguments(account=AccountTO, mobile_key=db.Key)
def create_jabber_account(account, mobile_key):
    settings = get_server_settings()
    if DEBUG and not settings.jabberAccountEndPoints:
        logging.warn('No jabber enpoints configured. Not creating jabber account.')
        return
    jabberEndpoint = choice(settings.jabberAccountEndPoints)
    payload = json.dumps(dict(username=account.user, server=account.server, password=account.password))
    challenge, data = encrypt_for_jabber_cloud(settings.jabberSecret.encode('utf8'), payload)
    response = urlfetch.fetch(url="http://%s/register" % jabberEndpoint,
                              payload=data, method="POST",
                              allow_truncated=False, follow_redirects=False, validate_certificate=False, deadline=30)
    azzert(response.status_code == 200,
           "Failed to create jabber account %s.\n\nStatus code: %s" % (account.account, response.status_code))
    success, signalNum, out, err = json.loads(
        decrypt_from_jabber_cloud(settings.jabberSecret.encode('utf8'), challenge, response.content))
    logging.info("success: %s\nexit_code or signal: %s\noutput: %s\nerror: %s" % (success, signalNum, out, err))

    if not success and "Error: conflict" in err:
        success = True
    if not success and " already registered at node " in out:
        success = True
    azzert(success, "Failed to create jabber account %s.\n\nOutput: %s" % (account.account, out))
    if mobile_key:
        try_or_defer(_mark_mobile_as_registered, mobile_key)


def _mark_mobile_as_registered(mobile_key):
    def trans():
        mobile = db.get(mobile_key)
        mobile.status = mobile.status | Mobile.STATUS_ACCOUNT_CREATED
        mobile.put()

    db.run_in_transaction(trans)


def registration_account_creation_response(sender, stanza):
    register_elements = stanza.getElementsByTagNameNS("mobicage:jabber", "register")
    register_element = register_elements[0]
    registration_id = register_element.getAttribute('registrationid')
    user = register_element.getAttribute('user')
    if not registration_id.startswith(user):
        return
    result_elements = stanza.getElementsByTagNameNS("mobicage:jabber", "result")
    azzert(len(result_elements) == 1)
    result_element = result_elements[0]
    if result_element.getAttribute('success') == "True":
        mobile = get_mobile_by_account(registration_id)
        mobile.status = mobile.status | Mobile.STATUS_ACCOUNT_CREATED
        mobile.put()
    else:
        error_message = result_element.getAttribute('error')
        error_message = "Account creation in ejabberd for registration with id = '%s' failed with message: '%s'." % (
            registration_id, error_message)
        logging.error(error_message)


@returns(AccountTO)
@arguments(user=unicode)
def generate_account(user=None):
    settings = get_server_settings()

    result = AccountTO()
    result.user = user or unicode(uuid.uuid1())
    result.server = settings.jabberDomain
    result.password = unicode(uuid.uuid4()) + unicode(uuid.uuid4())
    result.account = u'%s@%s' % (result.user, result.server)
    return result


def generate_welcome_message_flow(user_profile, app, welcome_message, signup_url):
    """
    Args:
        user_profile (rogerthat.models.UserProfile)
        app (App)
        welcome_message (unicode)
    """
    lang = user_profile.language or DEFAULT_LANGUAGE
    flow_params = {
        'branding_key': app.core_branding_hash,
        'language': lang,
        'welcome_message': welcome_message,
        'signup_url': signup_url
    }
    return JINJA_ENVIRONMENT.get_template('flows/welcome_message.xml').render(flow_params)


def send_welcome_message(user):
    def trans():
        signup_url = get_server_settings().signupUrl
        if not signup_url:
            logging.error('Will not send the welcome message, signup URL is not set')
            return

        ui = UserInteraction.get_by_key_name(user.email(), parent=parent_key(user)) or UserInteraction(
            key_name=user.email(), parent=parent_key(user))
        if not is_flag_set(UserInteraction.INTERACTION_WELCOME, ui.interactions):
            ui.interactions |= UserInteraction.INTERACTION_WELCOME
            db.put_async(ui)
            user_profile = get_user_profile(user)
            service_identity_user = add_slash_default(MC_DASHBOARD)
            parent_message_key = None
            app = get_app_by_id(user_profile.app_id)
            if app.type in (App.APP_TYPE_ENTERPRISE, App.APP_TYPE_YSAAA, App.APP_TYPE_CONTENT_BRANDING, App.APP_TYPE_SECURE_DEVICE):
                return None
            msg = localize_app_translation(user_profile.language, '_welcome_message', app.app_id, app_name=app.name,
                                           contact_email_address=app.get_contact_email_address())
            xml = generate_welcome_message_flow(user_profile, app, msg, signup_url)
            members = [user]
            push_message = msg.splitlines()[0]
            start_local_flow(service_identity_user, parent_message_key, xml, members, push_message=push_message,
                             check_friends=False)

    run_in_xg_transaction(trans)


@returns(Mobile)
@arguments(mobile_account=unicode, mobileInfo=MobileInfoTO, invitor_code=unicode, invitor_secret=unicode,
           anonymous_account=unicode)
def finish_registration(mobile_account, mobileInfo, invitor_code, invitor_secret, anonymous_account=None):
    from rogerthat.service.api import friends as service_api_friends
    m = get_mobile_by_account(mobile_account)
    mobile_key = m.key()
    ms_key = get_mobile_settings_cached(m).key()
    profile_key = get_user_profile_key(m.user)

    def trans():
        mobile, ms, my_profile = db.get((mobile_key, ms_key, profile_key))

        mobile.status = mobile.status | Mobile.STATUS_REGISTERED
        mobile.type = mobileInfo.app_type
        mobile.simCountry = mobileInfo.sim_country if mobileInfo.sim_country != MISSING else None
        mobile.simCountryCode = mobileInfo.sim_country_code if mobileInfo.sim_country_code != MISSING else None
        mobile.simCarrierCode = mobileInfo.sim_carrier_code if mobileInfo.sim_carrier_code != MISSING else None
        mobile.simCarrierName = mobileInfo.sim_carrier_name if mobileInfo.sim_carrier_name != MISSING else None
        mobile.netCountry = mobileInfo.net_country if mobileInfo.net_country != MISSING else None
        mobile.netCountryCode = mobileInfo.net_country_code if mobileInfo.net_country_code != MISSING else None
        mobile.netCarrierCode = mobileInfo.net_carrier_code if mobileInfo.net_carrier_code != MISSING else None
        mobile.netCarrierName = mobileInfo.net_carrier_name if mobileInfo.net_carrier_name != MISSING else None
        mobile.hardwareModel = mobileInfo.device_model_name
        mobile.osVersion = mobileInfo.device_os_version if mobileInfo.device_os_version != MISSING else None
        mobile.localeLanguage = mobileInfo.locale_language if mobileInfo.locale_language and mobileInfo.locale_language != MISSING else DEFAULT_LANGUAGE
        mobile.localeCountry = mobileInfo.locale_country
        mobile.timezone = mobileInfo.timezone if mobileInfo.timezone != MISSING else None
        mobile.timezoneDeltaGMT = mobileInfo.timezone_delta_gmt if mobileInfo.timezone_delta_gmt != MISSING else None

        if mobileInfo.app_major_version != MISSING and mobileInfo.app_minor_version != MISSING:
            ms.majorVersion = mobileInfo.app_major_version
            ms.minorVersion = mobileInfo.app_minor_version

        # This is the official place where we set the profile language
        my_profile.language = mobile.localeLanguage
        my_profile.country = mobile.netCountry or mobile.simCountry or mobile.localeCountry
        my_profile.timezone = mobile.timezone
        my_profile.timezoneDeltaGMT = mobile.timezoneDeltaGMT

        my_profile.mobiles = MobileDetails()
        my_profile.mobiles.addNew(mobile.account, mobile.type, mobile.pushId, mobile.app_id)

        put_and_invalidate_cache(mobile, ms, my_profile)

        deferred.defer(_finishup_mobile_registration, mobile, invitor_code, invitor_secret, ms_key,
                       _transactional=True, _queue=FAST_QUEUE)

        return mobile, my_profile

    mobile, my_profile = run_in_transaction(trans, xg=True)
    channel.send_message(mobile.user, u'com.mobicage.registration.finished')

    registration = get_registration_by_mobile(mobile)
    if registration and registration.installation:
        save_successful_registration(registration, mobile, my_profile)

        if registration.installation.service_identity_user and (registration.installation.qr_url or registration.installation.oauth_state):
            service_identity_user = registration.installation.service_identity_user
            service_user, service_identity = get_service_identity_tuple(service_identity_user)
            svc_profile = get_service_profile(service_user)
            user_details = [UserDetailsTO.fromUserProfile(my_profile)]
            user_app_id = get_app_id_from_app_user(mobile.user)

            # auto_connected_services
            services_to_connect = set()
            if registration.installation.service_callback_result == ACCEPT_AND_CONNECT_ID:
                def trans_update_app_id():
                    si = get_service_identity(service_identity_user)
                    bizz_check(si, "ServiceIdentity %s not found" % service_identity_user)
                    if user_app_id not in si.appIds:
                        si.appIds.append(user_app_id)
                        put_and_invalidate_cache(si)
                run_in_transaction(trans_update_app_id)
                services_to_connect.add(service_identity_user)

            for autoconnect_service_email in registration.installation.auto_connected_services:
                services_to_connect.add(add_slash_default(users.User(autoconnect_service_email)))

            for service_to_connect in services_to_connect:
                try_or_defer(makeFriends, mobile.user, service_to_connect, original_invitee=None, servicetag=None,
                             origin=None, notify_invitee=False, notify_invitor=False, user_data=None)

            # roles
            if registration.installation.roles:
                roles_to_add = defaultdict(set)
                for r in parse_complex_value(RegistrationResultRolesTO, json.loads(registration.installation.roles), True):
                    for role_id in r.ids:
                        roles_to_add[create_service_identity_user(
                            users.User(r.service), r.identity or ServiceIdentity.DEFAULT)].add(role_id)

                for service_identity_email, role_ids in roles_to_add.iteritems():
                    service_user, identity = get_service_identity_tuple(users.User(service_identity_email))
                    grant_service_roles(service_user, identity, mobile.user, list(role_ids))

            # callback
            if registration.installation.qr_url:
                service_api_friends.register_result(register_result_response_receiver, logServiceError, svc_profile,
                                                    service_identity=service_identity,
                                                    user_details=user_details,
                                                    origin=REGISTRATION_ORIGIN_QR)
            elif registration.installation.oauth_state:
                service_api_friends.register_result(register_result_response_receiver, logServiceError, svc_profile,
                                                    service_identity=service_identity,
                                                    user_details=user_details,
                                                    origin=REGISTRATION_ORIGIN_OAUTH)

        else:
            app = get_app_by_id(get_app_id_from_app_user(mobile.user))
            if app.admin_services:
                service_profiles = filter(None, db.get((get_profile_key(users.User(e)) for e in app.admin_services)))
                if service_profiles:
                    user_details = [UserDetailsTO.fromUserProfile(my_profile)]
                    for service_profile in service_profiles:
                        service_api_friends.register_result(register_result_response_receiver,
                                                            logServiceError,
                                                            service_profile,
                                                            service_identity=ServiceIdentity.DEFAULT,
                                                            user_details=user_details,
                                                            origin=REGISTRATION_ORIGIN_DEFAULT)

    if anonymous_account:
        deferred.defer(migrate_anonymous_account, anonymous_account, mobile.user)

    return mobile


@returns()
@arguments(anonymous_account=unicode, new_app_user=users.User)
def migrate_anonymous_account(anonymous_account, new_app_user):
    anonymous_mobile = get_mobile_by_account(anonymous_account)
    bizz_check(anonymous_mobile, 'No mobile found for this anonymous account: %s' % anonymous_account)

    anonymous_user = anonymous_mobile.user
    anonymous_friend_map, new_friend_map, anonymous_user_profile = db.get([get_friends_map_key_by_user(anonymous_user),
                                                                           get_friends_map_key_by_user(new_app_user),
                                                                           get_user_profile_key(anonymous_user)])
    bizz_check(anonymous_user_profile, 'No UserProfile found for %s', anonymous_user.email())

    if anonymous_friend_map:
        new_friend_details = new_friend_map.get_friend_details() if new_friend_map else {}
        for friend_detail in anonymous_friend_map.get_friend_details().values():
            if new_friend_map is None or friend_detail.email not in new_friend_details:
                logging.debug('Connecting %s to %s (%s)', new_app_user.email(), friend_detail.name, friend_detail.email)
                friend_user = users.User(friend_detail.email)
                user_data_str = None
                if friend_detail.hasUserData:
                    friend_user = add_slash_default(friend_user)
                    user_data_key = UserData.createKey(anonymous_user, friend_user)
                    user_data_str = db.get(user_data_key).data

                makeFriends(new_app_user, friend_user, friend_user, None, notify_invitee=False, notify_invitor=False,
                            origin=ORIGIN_USER_INVITE, user_data=user_data_str)

    deferred.defer(delete_user_data, anonymous_user, anonymous_friend_map, anonymous_user_profile)


def _finishup_mobile_registration_step2(mobile_key, invitor_code, invitor_secret):
    mobile = db.get(mobile_key)
    mobile_user = mobile.user
    server_settings = get_server_settings()

    def trans():  # Operates on 2 entity groups
        hookup_with_default_services.schedule(mobile_user)
        if invitor_code and invitor_secret:
            pp = ProfilePointer.get(invitor_code)
            if not pp:
                logging.error("User with userCode %s not found!" % invitor_code)
            else:
                deferred.defer(ack_invitation_by_invitation_secret, mobile_user, pp.user, invitor_secret,
                               _transactional=True, _countdown=10)

        elif invitor_code:
            for ysaaa_hash, static_email in chunks(server_settings.ysaaaMapping, 2):
                if invitor_code == ysaaa_hash:
                    service_user = users.User(static_email)
                    makeFriends(service_user, mobile_user, original_invitee=None, servicetag=None, origin=ORIGIN_YSAAA)
                    break
            else:
                azzert(False, u"ysaaa registration received but not found mapping")

        for _, static_email in chunks(server_settings.staticPinCodes, 2):
            if mobile_user.email() == static_email:
                break
        else:
            deferred.defer(send_messages_after_registration, mobile_key, _transactional=True)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


def _finishup_mobile_registration(mobile, invitor_code, invitor_secret, ms_key):
    mobile_user = mobile.user
    app_settings = get_app_settings(get_app_id_from_app_user(mobile_user))
    user_profile = get_user_profile(mobile_user)
    server_settings = get_server_settings()

    def trans():  # Operates on 2 entity groups
        email = get_human_user_from_app_user(mobile_user).email()
        for _, static_email in chunks(server_settings.staticPinCodes, 2):
            if email == static_email:
                break
        else:
            deferred.defer(send_welcome_message, mobile_user, _transactional=True, _countdown=5)

        mobile_settings = db.get(ms_key)
        request = UpdateSettingsRequestTO()
        request.settings = SettingsTO.fromDBSettings(app_settings, user_profile, mobile_settings)
        updateSettings(update_settings_response_handler, logError, mobile_user, request=request)

        deferred.defer(_finishup_mobile_registration_step2, mobile.key(), invitor_code, invitor_secret,
                       _transactional=True, _queue=FAST_QUEUE)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


def get_mobile_type(platform, use_xmpp_kick, use_firebase_kick_channel=False):
    if platform == "android":
        if use_firebase_kick_channel:
            mobile_type = Mobile.TYPE_ANDROID_FIREBASE_HTTP
        else:
            mobile_type = Mobile.TYPE_ANDROID_HTTP
    elif platform == "iphone":
        if use_xmpp_kick is None:
            mobile_type = Mobile.TYPE_LEGACY_IPHONE_XMPP
        elif use_xmpp_kick == "true":
            mobile_type = Mobile.TYPE_IPHONE_HTTP_XMPP_KICK
        else:
            mobile_type = Mobile.TYPE_IPHONE_HTTP_APNS_KICK
    elif platform == "windows_phone":
        mobile_type = Mobile.TYPE_WINDOWS_PHONE
    else:
        logging.warn("Unknown platform: '%s'" % platform)
        return
    return mobile_type


def get_or_insert_installation(install_id, version, mobile_type, timestamp, app_id, language, status=None):
    timestamp = long(timestamp)
    installation = Installation.get_by_key_name(install_id)
    if not installation:
        installation = Installation(key_name=install_id,
                                    version=unicode(version),
                                    platform=mobile_type,
                                    timestamp=timestamp,
                                    app_id=app_id,
                                    status=status or InstallationStatus.STARTED)
        log = InstallationLog(parent=installation,
                              timestamp=timestamp,
                              description='Installed with language %s and app_id %s' % (language, app_id))
        db.put([installation, log])
        send_installation_progress_callback(installation, [log])
    elif status and installation.status != status:
        installation.status = status
        installation.put()
    return installation


def save_successful_registration(registration, mobile, my_profile):
    installation = registration.installation
    installation.mobile = mobile
    installation.profile = my_profile
    installation.status = InstallationStatus.FINISHED
    log = InstallationLog(parent=installation, timestamp=now(), description='Registration successful.')
    send_installation_progress_callback(installation, [log])
    db.put([log, installation])


@returns()
@arguments(installation=Installation, logs=[InstallationLog])
def _send_installation_progress_callback(installation, logs):
    app = get_app_by_id(installation.app_id)
    if not app:
        return

    admin_services = app.admin_services
    if not admin_services:
        return

    profiles = get_profiles(map(users.User, admin_services))
    installation_to = InstallationTO.from_model(installation, installation.mobile, installation.profile)
    logs_to = [InstallationLogTO.from_model(log) for log in logs]
    rpcs = []
    for service_profile in profiles:
        rpc = installation_progress(installation_progress_response_receiver, logServiceError, service_profile,
                                    installation=installation_to, logs=logs_to, DO_NOT_SAVE_RPCCALL_OBJECTS=True)
        if rpc:
            rpcs.append(rpc)
    if rpcs:
        db.put(rpcs)


@returns()
@arguments(installation=Installation, logs=[InstallationLog])
def send_installation_progress_callback(installation, logs):
    if installation:
        deferred.defer(_send_installation_progress_callback, installation, logs, _transactional=db.is_in_transaction())
