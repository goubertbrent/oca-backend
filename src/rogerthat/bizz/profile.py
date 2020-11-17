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
import datetime
import hashlib
from httplib import HTTPException
import json
import logging
import os
import re
from types import NoneType
import types

from google.appengine.api import images, urlfetch, search
from google.appengine.api.urlfetch_errors import DeadlineExceededError
from google.appengine.ext import db, deferred

import facebook
from mcfw.cache import invalidate_cache
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from mcfw.utils import chunks
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.friends import INVITE_ID, INVITE_FACEBOOK_FRIEND, invite, breakFriendShip, makeFriends, userCode
from rogerthat.bizz.job import run_job
from rogerthat.bizz.maps.services import cleanup_map_index
from rogerthat.bizz.messaging import sendMessage
from rogerthat.bizz.session import drop_sessions_of_user
from rogerthat.bizz.system import get_identity, identity_update_response_handler
from rogerthat.bizz.user import reactivate_user_profile
from rogerthat.capi.system import identityUpdate
from rogerthat.consts import MC_DASHBOARD
from rogerthat.dal import parent_key, put_and_invalidate_cache, app
from rogerthat.dal.app import get_app_name_by_id, get_app_by_user, get_app_by_id
from rogerthat.dal.broadcast import get_broadcast_settings_flow_cache_keys_of_user
from rogerthat.dal.friend import get_friends_map
from rogerthat.dal.profile import get_avatar_by_id, get_existing_profiles_via_facebook_ids, \
    get_existing_user_profiles, get_user_profile, get_profile_infos, get_profile_info, get_service_profile, \
    get_user_profiles, get_service_or_user_profile, get_deactivated_user_profile
from rogerthat.dal.service import get_default_service_identity_not_cached, get_all_service_friend_keys_query, \
    get_service_identities_query, get_all_archived_service_friend_keys_query, get_friend_serviceidentity_connection
from rogerthat.models import FacebookUserProfile, Avatar, ProfilePointer, ShortURL, FacebookProfilePointer, \
    FacebookDiscoveryInvite, Message, ServiceProfile, UserProfile, ServiceIdentity, ProfileInfo, \
    App, \
    Profile, SearchConfig, FriendServiceIdentityConnectionArchive, \
    UserData, UserDataArchive, ActivationLog, ProfileHashIndex
from rogerthat.rpc import users
from rogerthat.rpc.models import Mobile
from rogerthat.rpc.rpc import logError, SKIP_ACCOUNTS
from rogerthat.rpc.service import BusinessException
from rogerthat.to.friends import FacebookRogerthatProfileMatchTO
from rogerthat.to.messaging import ButtonTO, UserMemberTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.to.system import IdentityUpdateRequestTO
from rogerthat.translations import localize, DEFAULT_LANGUAGE
from rogerthat.utils import now, urlencode, is_clean_app_user_email, get_epoch_from_datetime,\
    get_python_stack_trace
from rogerthat.utils.app import get_app_id_from_app_user, create_app_user, get_human_user_from_app_user, \
    get_app_user_tuple, create_app_user_by_email
from rogerthat.utils.channel import send_message
from rogerthat.utils.service import create_service_identity_user, remove_slash_default
from rogerthat.utils.transactions import on_trans_committed, run_in_transaction


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

CURRENT_DIR = os.path.dirname(__file__)

UNKNOWN_AVATAR_PATH = os.path.join(CURRENT_DIR, 'unknown_avatar.png')
NUNTIUZ_AVATAR_PATH = os.path.join(CURRENT_DIR, 'nuntiuz.png')

USER_INDEX = "USER_INDEX"


class FailedToBuildFacebookProfileException(BusinessException):
    pass


def get_unknown_avatar():
    f = open(UNKNOWN_AVATAR_PATH, "rb")
    try:
        return f.read()
    finally:
        f.close()


def get_nuntiuz_avatar():
    f = open(NUNTIUZ_AVATAR_PATH, "rb")
    try:
        return f.read()
    finally:
        f.close()

UNKNOWN_AVATAR = get_unknown_avatar()
NUNTIUZ_AVATAR = get_nuntiuz_avatar()


@returns(NoneType)
@arguments(app_user=users.User)
def schedule_re_index(app_user):
    # Does NOT have to be transactional, running it over and over does not harm
    deferred.defer(_re_index, app_user)


def create_user_index_document(index, app_user_email, fields):
    email_encoded = 'base64:' + base64.b64encode(app_user_email)
    doc = search.Document(doc_id=email_encoded, fields=fields)
    return index.put(doc)[0]


def delete_user_index_document(index, app_user_email):
    email_encoded = 'base64:' + base64.b64encode(app_user_email)
    return index.delete(email_encoded)[0]


def _re_index(app_user):
    from rogerthat.bizz.messaging import re_index_conversations_of_member

    def trans():
        user_profile = get_profile_info(app_user, False)
        fm = get_friends_map(app_user)
        return user_profile, fm
    user_profile, fm = db.run_in_transaction(trans)

    app_user_email = app_user.email()
    # delete old indexed app user if the doc_id is app_user_email (not encoded)
    user_index = search.Index(name=USER_INDEX)
    try:
        if user_index.get(app_user_email):
            user_index.delete(app_user_email)
    except search.InvalidRequest:
        pass

    deferred.defer(re_index_conversations_of_member, app_user_email)

    if not user_profile:
        logging.info("Tried to index a user who is deactivated")
        delete_user_index_document(user_index, app_user_email)
        return

    if user_profile.isServiceIdentity:
        logging.error("Tried to index a service into the USER_INDEX")
        return

    connections = StringIO()
    for f in fm.friends:
        email = f.email().encode('utf8').replace('"', '')
        connections.write('@@%s@@' % email)
        if '/' in email:
            connections.write('@@%s@@' % email.split('/')[0])

    human_user, app_id = get_app_user_tuple(app_user)

    fields = [
        search.TextField(name='email', value=human_user.email()),
        search.TextField(name='name', value=user_profile.name),
        search.TextField(name='language', value=user_profile.language),
        search.TextField(name='connections', value=connections.getvalue()),
        search.TextField(name='app_id', value=app_id)
    ]

    if user_profile.profileData:
        data = json.loads(user_profile.profileData)
        for key, value in data.iteritems():
            fields.append(search.TextField(name='pd_%s' % key.replace(' ', '_'), value=value))

    create_user_index_document(user_index, app_user_email, fields)


@returns([UserDetailsTO])
@arguments(name_or_email_term=unicode, app_id=unicode)
def search_users_via_name_or_email(name_or_email_term, app_id=None):
    logging.info("Looking for users with term '%s'." % name_or_email_term)
    if len(name_or_email_term) < 3:
        logging.info("Search term is to short. Bye bye.")
        return []
    name_or_email_term = name_or_email_term.replace('"', '')
    if app_id:
        query = search.Query(query_string='email:"%s" OR name:"%s" app_id:%s' % (name_or_email_term, name_or_email_term, app_id),
                             options=search.QueryOptions(returned_fields=['email', 'name', 'language', 'app_id'], limit=10))
    else:
        query = search.Query(query_string='email:"%s" OR name:"%s"' % (name_or_email_term, name_or_email_term),
                             options=search.QueryOptions(returned_fields=['email', 'name', 'language', 'app_id'], limit=10))
    search_result = search.Index(name=USER_INDEX).search(query)
    return [UserDetailsTO.create(email=doc.fields[0].value,
                                 name=doc.fields[1].value,
                                 language=doc.fields[2].value,
                                 app_id=doc.fields[3].value,
                                 avatar_url=None)
            for doc in search_result.results]


@returns([UserDetailsTO])
@arguments(connection=unicode, name_or_email_term=unicode, app_id=unicode, include_avatar=bool)
def search_users_via_friend_connection_and_name_or_email(connection, name_or_email_term, app_id=None, include_avatar=False):
    """Search for users in the USER_INDEX.
    connection: The account of the connection (human or service).
        In case of a service searching across identities is possible via ommiting the slash and everything after it.
    name_or_email_term: A fragment of the name or email of the user you are looking for."""
    if len(name_or_email_term) < 3:
        return []
    connection = connection.encode('utf8').replace('"', '')
    name_or_email_term = name_or_email_term.replace('"', '')
    if app_id:
        query = search.Query(query_string='connections:"@@%s@@" AND (email:"%s" OR name:"%s") app_id:%s' % (connection, name_or_email_term, name_or_email_term, app_id),
                             options=search.QueryOptions(returned_fields=['email', 'name', 'language', 'app_id'], limit=10))
    else:
        query = search.Query(query_string='connections:"@@%s@@" AND (email:"%s" OR name:"%s")' % (connection, name_or_email_term, name_or_email_term),
                             options=search.QueryOptions(returned_fields=['email', 'name', 'language', 'app_id'], limit=10))
    search_result = search.Index(name=USER_INDEX).search(query)

    avatar_urls = dict()
    if include_avatar:
        for p in get_user_profiles([create_app_user_by_email(d.fields[0].value, d.fields[3].value)
                                    for d in search_result.results]):
            avatar_urls[p.user] = p.avatarUrl

    def create_user_detail(doc):
        if include_avatar:
            avatar_url = avatar_urls.get(create_app_user_by_email(d.fields[0].value, d.fields[3].value))
        else:
            avatar_url = None
        return UserDetailsTO.create(email=d.fields[0].value,
                                    name=doc.fields[1].value,
                                    language=doc.fields[2].value,
                                    avatar_url=avatar_url,
                                    app_id=doc.fields[3].value)

    return [create_user_detail(d) for d in search_result.results]


@returns(UserProfile)
@arguments(email=unicode, language=unicode, name=unicode)
def get_profile_for_google_user(email, language, name):
    user = users.User(email)
    user_profile = get_user_profile(user)
    if not user_profile:
        user_profile = UserProfile(parent=parent_key(user), key_name=user.email())
        user_profile.name = name if name else user.email()
        user_profile.first_name = None
        user_profile.last_name = None
        user_profile.language = language
        user_profile.version = 1
        put_and_invalidate_cache(user_profile, ProfilePointer.create(user))
        update_friends(user_profile, [u"name", u"language"])
    return user_profile


@returns(Avatar)
@arguments(app_user=users.User, fb_id=unicode, profile_or_key=(Profile, db.Key), avatar_or_key=(Avatar, db.Key),
           retry_count=int)
def _get_and_save_facebook_avatar(app_user, fb_id, profile_or_key, avatar_or_key, retry_count=0):
    if retry_count == 5:
        logging.debug("Reached max retry count. Giving up trying to get the facebook avatar for %s.", app_user)
        return None

    avatar = db.get(avatar_or_key) if isinstance(avatar_or_key, db.Key) else avatar_or_key
    if avatar.picture:
        logging.debug("In the mean time, there already is an avatar set for %s. Stop retrying...", app_user)
        return avatar

    profile_or_key_is_key = isinstance(profile_or_key, db.Key)
    try:
        url = 'https://graph.facebook.com/%s/picture?width=300&height=300' % fb_id
        response = urlfetch.fetch(url, deadline=60)  # type: urlfetch._URLFetchResult
        if response.status_code == 404:
            logging.warn('Facebook avatar not found. Giving up trying to get the facebook avatar for %s', app_user)
            return None
        if response.status_code != 200:
            logging.warn('Recieved code %s from facebook while fetching avatar. Retrying... \n%s', response.status_code,
                         response.content)
            profile_key = profile_or_key if profile_or_key_is_key else profile_or_key.key()
            deferred.defer(_get_and_save_facebook_avatar, app_user, fb_id, profile_key, avatar.key(), retry_count + 1,
                           _countdown=5)
            return None
        image = response.content

        def update_avatar_and_profile(profile_or_key_is_key):
            avatar = db.get(avatar_or_key) if isinstance(avatar_or_key, db.Key) else avatar_or_key
            if avatar.picture:
                logging.debug("In the mean time, there already is an avatar set for %s. Stopping...", app_user)
                return None
            avatar.picture = image
            avatar.put()

            profile = db.get(profile_or_key) if profile_or_key_is_key else profile_or_key
            _calculateAndSetAvatarHash(profile, image)
            if profile_or_key_is_key:
                profile.put()
            return avatar

        if profile_or_key_is_key:
            xg_on = db.create_transaction_options(xg=True)
            avatar = db.run_in_transaction_options(xg_on, update_avatar_and_profile, profile_or_key_is_key)
        else:
            avatar = update_avatar_and_profile(profile_or_key_is_key)

    except Exception as e:
        avatar.put()  # put empty to get avatar id.

        if isinstance(e, DeadlineExceededError) or isinstance(e, HTTPException) and e.message and 'deadline' in e.message.lower():
            logging.debug("Timeout while retrieving facebook avatar for %s. Retrying...", app_user)
            profile_key = profile_or_key if profile_or_key_is_key else profile_or_key.key()
            deferred.defer(_get_and_save_facebook_avatar, app_user, fb_id, profile_key, avatar.key(), retry_count + 1,
                           _countdown=5)
        else:
            logging.exception("Failed to retrieve facebook avatar for %s.", app_user)

    return avatar


@returns(UserProfile)
@arguments(access_token=unicode, app_user=users.User, update=bool, language=unicode, app_id=unicode,
           community_id=(int, long))
def get_profile_for_facebook_user(access_token, app_user, update=False, language=DEFAULT_LANGUAGE, app_id=App.APP_ID_ROGERTHAT,
                                  community_id=0):
    gapi = facebook.GraphAPI(access_token, version='2.12')
    fields = ["id", "first_name", "last_name", "name", "verified", "locale", "gender", "email", "birthday", "link"]
    fb_profile = gapi.get_object("me", fields=','.join(fields))
    logging.debug("/me graph response: %s", fb_profile)

    if not app_user:
        if "email" in fb_profile:
            app_user = create_app_user(users.User(fb_profile["email"]), app_id)
        else:
            raise FailedToBuildFacebookProfileException(
                localize(language, 'There is no e-mail address configured in your facebook account. Please use the e-mail based login.'))

        # TODO we should validate app.user_regex
        # TODO we should check if email is not used for a service account

    couple_facebook_id_with_profile(app_user, access_token)
    profile = get_user_profile(app_user)
    if not profile or update:
        if not profile:
            profile = FacebookUserProfile(parent=parent_key(app_user), key_name=app_user.email())
            profile.app_id = app_id
            app = get_app_by_id(app_id)
            if community_id == 0:
                azzert(len(app.community_ids) == 1, "Community was NOT provided but len(app.community_ids) != 1")
                community_id = app.community_ids[0]
            else:
                azzert(community_id in app.community_ids, "Community was provided but not found in app.community_ids")
            profile.community_id = community_id
            avatar = Avatar(user=app_user)
        else:
            avatar = get_avatar_by_id(profile.avatarId)
            if not avatar:
                avatar = Avatar(user=app_user)

        profile.first_name = None
        profile.last_name = None
        if fb_profile.get("first_name"):
            profile.first_name = fb_profile["first_name"]
            profile.last_name = fb_profile.get("last_name") or u""
            profile.name = u'%s %s' % (profile.first_name, profile.last_name)
        elif fb_profile.get("name"):
            profile.name = fb_profile["name"]
        else:
            profile.name = get_human_user_from_app_user(app_user).email().replace("@", " at ")

        if profile.birthdate is None and fb_profile.get("birthday"):
            birthday = fb_profile["birthday"].split("/")
            date = datetime.date(int(birthday[2]), int(birthday[0]), int(birthday[1]))
            profile.birthdate = get_epoch_from_datetime(date)
            logging.debug('Set profile birthdate from facebook: %s', date)

        if profile.gender is None and fb_profile.get("gender"):
            gender = fb_profile["gender"]
            if gender == "male":
                profile.gender = UserProfile.GENDER_MALE
            elif gender == "female":
                profile.gender = UserProfile.GENDER_FEMALE
            else:
                profile.gender = UserProfile.GENDER_CUSTOM
            logging.debug('Set gender from facebook: %s', profile.gender_str)

        avatar = _get_and_save_facebook_avatar(app_user, fb_profile["id"], profile, avatar)
        if not avatar:
            avatar = Avatar(user=app_user)
            avatar.put()

        profile.avatarId = avatar.key().id()
        profile.language = language
        profile.profile_url = fb_profile.get("link")
        profile.access_token = access_token
        profile.version = 1
        put_and_invalidate_cache(profile, ProfilePointer.create(app_user))
        update_friends(profile, [u"name", u"avatar"])
        update_mobiles(app_user, profile)
    return profile


@returns(NoneType)
@arguments(app_user=users.User, access_token=unicode)
def couple_facebook_id_with_profile(app_user, access_token):
    deferred.defer(_couple_facebook_id_with_profile, app_user, access_token)


def _couple_facebook_id_with_profile(app_user, access_token):
    try:
        gapi = facebook.GraphAPI(access_token)
        fb_profile = gapi.get_object("me")
    except facebook.GraphAPIError, e:
        if e.type == "OAuthException":
            # throwing a BusinessException(PermanentTaskFailure) will make sure the task won't retry and keep failing
            raise BusinessException("Giving up because we caught an OAuthException: %s" % e)
        else:
            raise e
    FacebookProfilePointer(key_name=fb_profile["id"], user=app_user).put()
    _discover_registered_friends_via_facebook_profile(app_user, access_token)


def _discover_registered_friends_via_facebook_profile(app_user, access_token):
    facebook_friends = get_friend_list_from_facebook(access_token)
    friend_ids = list({f['id'] for f in facebook_friends})
    matches = get_existing_profiles_via_facebook_ids(friend_ids, get_app_id_from_app_user(app_user))
    invites_sent = db.get([db.Key.from_path(FacebookDiscoveryInvite.kind(), rtId.email(), parent=parent_key(app_user))
                           for _, rtId in matches])
    new_invites = list()
    for match, invite in zip(matches, invites_sent):
        fb_friend_user = match[1]
        if invite:
            logging.debug('%s and %s are already coupled in the past',
                          app_user.email(), fb_friend_user.email())
        else:
            logging.info('Creating friend connection between %s and %s because they\'re friends on facebook',
                         app_user.email(), fb_friend_user.email())
            new_invites.append(FacebookDiscoveryInvite(key_name=fb_friend_user.email(), parent=parent_key(app_user)))
            deferred.defer(makeFriends, app_user, fb_friend_user, fb_friend_user, servicetag=None, origin=None,
                           notify_invitee=False, notify_invitor=False, _countdown=30)
    if new_invites:
        db.put_async(new_invites)


def _send_message_to_inform_user_about_a_new_join(new_user, fb_friend_user):
    def trans():
        key_name = fb_friend_user.email()
        parent = parent_key(new_user)
        invite = FacebookDiscoveryInvite.get_by_key_name(key_name, parent)
        if invite:
            return
        db.put_async(FacebookDiscoveryInvite(key_name=key_name, parent=parent))
        friend_map = get_friends_map(new_user)
        if fb_friend_user in friend_map.friends:
            return
        deferred.defer(_send_message_to_inform_user_about_a_new_join_step_2,
                       fb_friend_user, new_user, _transactional=True)
    db.run_in_transaction(trans)


def _send_message_to_inform_user_about_a_new_join_step_2(fb_friend_user, new_user):
    new_user_profile, fb_friend_profile = get_profile_infos(
        [new_user, fb_friend_user], expected_types=[UserProfile, UserProfile])
    azzert(new_user_profile.app_id == fb_friend_profile.app_id)
    app_name = get_app_name_by_id(new_user_profile.app_id)
    to_language = fb_friend_profile.language if fb_friend_profile else DEFAULT_LANGUAGE
    message_text = localize(
        to_language, "%(name)s just joined %(app_name)s, and we found you in his facebook friends list!", name=new_user_profile.name, app_name=app_name)
    button = ButtonTO()
    button.id = INVITE_ID
    button.caption = localize(
        to_language, "Invite %(name)s to connect on %(app_name)s", name=new_user_profile.name, app_name=app_name)
    button.action = None
    button.ui_flags = 0

    def trans():
        message = sendMessage(MC_DASHBOARD, [UserMemberTO(fb_friend_user)], Message.FLAG_ALLOW_DISMISS, 0, None,
                              message_text, [button], None, get_app_by_user(fb_friend_user).core_branding_hash,
                              INVITE_FACEBOOK_FRIEND, is_mfr=False)
        message.invitor = fb_friend_user
        message.invitee = new_user
        message.put()
    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


@returns(NoneType)
@arguments(message=Message)
def ack_facebook_invite(message):
    azzert(message.tag == INVITE_FACEBOOK_FRIEND)
    memberStatus = message.memberStatusses[message.members.index(message.invitor)]
    if not memberStatus.dismissed and message.buttons[memberStatus.button_index].id == INVITE_ID:
        profile = get_user_profile(message.invitee)
        if profile:
            invite(message.invitor, message.invitee.email(), None, profile.language, None, None,
                   get_app_id_from_app_user(message.invitor))
        else:
            logging.info('Invitee\'s profile doesn\'t exist anymore: %s', message.invitee)


@returns(int)
@arguments(user_code=unicode)
def create_short_url(user_code):
    su = ShortURL()
    su.full = "/q/i" + user_code
    su.put()
    return su.key().id()


@returns([ShortURL])
@arguments(app_id=unicode, amount=(int, long))
def generate_unassigned_short_urls(app_id, amount):
    @db.non_transactional
    def allocate_ids():
        return db.allocate_ids(db.Key.from_path(ShortURL.kind(), 1), amount)  # (start, end)

    result = list()
    id_range = allocate_ids()
    for short_url_id in xrange(id_range[0], id_range[1] + 1):
        user_code = userCode(users.User("%s@%s" % (short_url_id, app_id)))
        result.append(ShortURL(key=db.Key.from_path(ShortURL.kind(), short_url_id), full="/q/i" + user_code))

    for c in chunks(result, 200):
        db.put(c)
    return result


def _validate_name(name):
    if name is None:
        raise ValueError("Name can not be null")
    if not name:
        raise ValueError("Name can not be empty")
    name = name.strip().replace('@', ' at ')
    if len(name) > 50:
        raise ValueError("Name can not be longer than 50 characters. name: '%s' length: %s " % (name, len(name)))
    return name


def _create_new_avatar(user, image=None):
    avatar = Avatar(user=user)
    image = UNKNOWN_AVATAR if not image else base64.b64decode(image)
    avatar.picture = db.Blob(image)
    avatar.put()
    return avatar, image


@returns(UserProfile)
@arguments(app_user=users.User, name=unicode, language=unicode, ysaaa=bool, owncloud_password=unicode, image=unicode,
           tos_version=(int, long, NoneType), consent_push_notifications_shown=bool, first_name=unicode, last_name=unicode,
           community_id=(int, long))
def create_user_profile(app_user, name, language=None, ysaaa=False, owncloud_password=None, image=None,
                        tos_version=None, consent_push_notifications_shown=False, first_name=None, last_name=None,
                        community_id=0):
    name = _validate_name(name)

    # todo communities remove after testing
    app_id = get_app_id_from_app_user(app_user)
    app_model = get_app_by_id(app_id)
    if community_id:
        azzert(community_id in app_model.community_ids, "Community was provided but not found in app.community_ids")
    else:
        stack_stace = get_python_stack_trace(short=False)
        logging.error("create_user_profile community_id was not provided %s", stack_stace)
        azzert(len(app_model.community_ids) == 1, "Community was NOT provided but len(app.community_ids) != 1")
        community_id = app_model.community_ids[0]

    def trans_create(avatar_image):
        azzert(not get_user_profile(app_user, cached=False))

        avatar, image = _create_new_avatar(app_user, avatar_image)

        user_profile = UserProfile(parent=parent_key(app_user), key_name=app_user.email())
        if name:
            user_profile.name = name
            user_profile.first_name = None
            user_profile.last_name = None
        if first_name or last_name:
            user_profile.first_name = first_name or u''
            user_profile.last_name = last_name or u''
            user_profile.name = u'%s %s' % (user_profile.first_name, user_profile.last_name)
        user_profile.language = language
        user_profile.avatarId = avatar.key().id()
        user_profile.app_id = get_app_id_from_app_user(app_user)
        user_profile.owncloud_password = owncloud_password
        if tos_version:
            user_profile.tos_version = tos_version
        if consent_push_notifications_shown:
            user_profile.consent_push_notifications_shown = True
        user_profile.community_id = community_id
        _calculateAndSetAvatarHash(user_profile, image)

        put_and_invalidate_cache(user_profile, ProfilePointer.create(app_user), ProfileHashIndex.create(app_user))

        return user_profile

    user_profile = run_in_transaction(trans_create, True, image)
    if not ysaaa:
        schedule_re_index(app_user)
    return user_profile


@returns(tuple)
@arguments(service_user=users.User, url=unicode, email=unicode)
def put_loyalty_user(service_user, url, email):
    short_url = None  # ShortURL
    url_regex = re.match("(HTTPS?://)(.*)/(M|S)/(.*)", url.upper())
    if url_regex:
        from rogerthat.pages.shortner import get_short_url_by_code
        code = url_regex.group(4)
        short_url = get_short_url_by_code(code)
        if short_url and not short_url.full.startswith("/q/i"):
            short_url = None

    if not short_url:
        service_profile = get_service_profile(service_user)
        community = get_community(service_profile.community_id)
        logging.debug('Create new unassigned short url, because the provided loyalty user URL is unknown (%s)', url)
        short_url = generate_unassigned_short_urls(community.default_app, 1)[0]
        url = short_url.full

    user_code = short_url.full[4:]
    pp = ProfilePointer.get(user_code)
    if pp:
        app_user = pp.user
    else:
        service_profile = get_service_profile(service_user)
        community = get_community(service_profile.community_id)
        app_user = put_loyalty_user_profile(email.strip(), community.default_app, user_code, short_url.key().id(),
                                            service_profile.defaultLanguage, service_profile.community_id)

    return url, app_user


@returns(users.User)
@arguments(email=unicode, app_id=unicode, user_code=unicode, short_url_id=(int, long), language=unicode, community_id=(int, long))
def put_loyalty_user_profile(email, app_id, user_code, short_url_id, language, community_id=0):
    app_user = create_app_user(users.User(email), app_id)
    name = _validate_name(email)

    def trans_create():
        rogerthat_profile = get_service_or_user_profile(users.User(email))
        if rogerthat_profile and isinstance(rogerthat_profile, ServiceProfile):
            from rogerthat.bizz.service import AppFailedToCreateUserProfileWithExistingServiceException
            raise AppFailedToCreateUserProfileWithExistingServiceException(email)

        user_profile = get_user_profile(app_user, cached=False)
        is_new_profile = False
        if not user_profile:
            deactivated_user_profile = get_deactivated_user_profile(app_user)
            if deactivated_user_profile:
                deferred.defer(reactivate_user_profile, deactivated_user_profile, app_user, community_id=community_id, _transactional=True)
                ActivationLog(timestamp=now(), email=app_user.email(), mobile=None,
                              description="Reactivate user account by registering a paper loyalty card").put()
            else:
                is_new_profile = True
                avatar, image = _create_new_avatar(app_user)

                user_profile = UserProfile(parent=parent_key(app_user), key_name=app_user.email())
                user_profile.name = name
                user_profile.first_name = None
                user_profile.last_name = None
                user_profile.language = language
                user_profile.avatarId = avatar.key().id()
                user_profile.app_id = app_id
                user_profile.community_id = community_id
                _calculateAndSetAvatarHash(user_profile, image)

        pp = ProfilePointer(key=db.Key.from_path(ProfilePointer.kind(), user_code))
        pp.user = app_user
        pp.short_url_id = short_url_id

        if is_new_profile:
            put_and_invalidate_cache(user_profile, pp, ProfilePointer.create(app_user))
        else:
            pp.put()

    run_in_transaction(trans_create, True)
    schedule_re_index(app_user)

    return app_user


@returns(tuple)
@arguments(service_user=users.User, name=unicode, update_func=types.FunctionType, community_id=(int, long))
def create_service_profile(service_user, name, update_func=None, community_id=0):
    from rogerthat.bizz.service import create_default_qr_templates
    from rogerthat.bizz.news import create_default_news_settings

    name = _validate_name(name)

    if community_id:
        community = get_community(community_id)
        default_app_id = community.default_app
    else:
        default_app = app.get_default_app()
        default_app_id = default_app.app_id if default_app else App.APP_ID_ROGERTHAT

        # todo communities remove after testing
        stack_stace =  get_python_stack_trace(short=False)
        logging.error("create_service_profile community_id was not provided %s", stack_stace)
        app_model = get_app_by_id(default_app_id)
        azzert(len(app_model.community_ids) == 1, "Community was NOT provided but len(app.community_ids) != 1")
        community_id = app_model.community_ids[0]

    def trans_prepare_create():
        avatar, image = _create_new_avatar(service_user)

        from rogerthat.bizz.service import _create_recommendation_qr_code
        share_sid_key = _create_recommendation_qr_code(service_user, ServiceIdentity.DEFAULT, default_app_id)

        return avatar, image, share_sid_key

    def trans_create(avatar, image, share_sid_key):
        azzert(not get_service_profile(service_user, cached=False))
        azzert(not get_default_service_identity_not_cached(service_user))

        profile = ServiceProfile(parent=parent_key(service_user), key_name=service_user.email())
        profile.avatarId = avatar.key().id()
        profile.community_id = community_id
        _calculateAndSetAvatarHash(profile, image)

        service_identity_user = create_service_identity_user(service_user, ServiceIdentity.DEFAULT)
        service_identity = ServiceIdentity(key=ServiceIdentity.keyFromUser(service_identity_user))
        service_identity.inheritanceFlags = 0
        service_identity.name = name
        service_identity.description = "%s (%s)" % (name, service_user.email())
        service_identity.shareSIDKey = share_sid_key
        service_identity.shareEnabled = False
        service_identity.creationTimestamp = now()
        service_identity.defaultAppId = default_app_id
        service_identity.appIds = [default_app_id]

        update_result = update_func(profile, service_identity) if update_func else None

        put_and_invalidate_cache(profile, service_identity,
                                 ProfilePointer.create(service_user),
                                 ProfileHashIndex.create(service_user))

        deferred.defer(create_default_qr_templates, service_user, _transactional=True)
        deferred.defer(create_default_news_settings, service_user, profile.organizationType, profile.community_id,
                       _transactional=True)

        return profile, service_identity, update_result

    avatar, image, share_sid_key = run_in_transaction(trans_prepare_create, True)
    try:
        profile, service_identity, update_result = run_in_transaction(trans_create, True, avatar, image, share_sid_key)
        return (profile, service_identity, update_result) if update_func else (profile, service_identity)
    except:
        db.delete([avatar, share_sid_key])
        raise


def update_password_hash(profile, passwordHash, lastUsedMgmtTimestamp):
    profile.passwordHash = passwordHash
    profile.lastUsedMgmtTimestamp = lastUsedMgmtTimestamp
    profile.put()


def update_user_profile(app_user, name, image, language):
    def trans():
        user_profile = get_user_profile(app_user)
        changed_properties = []
        if user_profile.language != language:
            user_profile.language = language
            changed_properties.append(u"language")
            db.delete_async(get_broadcast_settings_flow_cache_keys_of_user(app_user))
        if user_profile.name != name:
            changed_properties.append(u"name")
            user_profile.name = name
            user_profile.first_name = None
            user_profile.last_name = None
        if image:
            _update_avatar(user_profile, image)
            changed_properties.append(u"avatar")
        user_profile.version += 1
        user_profile.put()

        update_mobiles(app_user, user_profile)  # update myIdentity
        update_friends(user_profile, changed_properties)  # notify my friends

        return user_profile

    user_profile = run_in_transaction(trans, xg=True)
    schedule_re_index(app_user)
    return user_profile


def update_service_profile(service_user, image):
    from rogerthat.bizz.job.update_friends import schedule_update_all_friends_of_service_user

    def trans():
        service_profile = get_service_profile(service_user)
        if image:
            _update_avatar(service_profile, image)
        service_profile.version += 1
        service_profile.put()

        schedule_update_all_friends_of_service_user(service_profile)
    return run_in_transaction(trans, True)


def _update_avatar(profile, image):
    _meta, img_b64 = image.split(',')
    image_bytes = base64.b64decode(img_b64)

    img = images.Image(str(image_bytes))
    img.resize(150, 150)

    avatar = get_avatar_by_id(profile.avatarId)
    if not avatar:
        avatar = Avatar(user=profile.user)
    image = img.execute_transforms(images.PNG, 100)
    update_avatar_profile(profile, avatar, image)


@returns(NoneType)
@arguments(service_user=users.User, image=str)
def update_service_avatar(service_user, image):
    img = images.Image(image)
    img.im_feeling_lucky()
    img.execute_transforms()
    if img.height != img.width:
        devation = float(img.width) / float(img.height)
        if devation < 0.95 or devation > 1.05:
            from rogerthat.bizz.service import AvatarImageNotSquareException
            logging.debug("Avatar Size: %sx%s" % (img.width, img.height))
            raise AvatarImageNotSquareException()
    img = images.Image(image)
    img.resize(150, 150)
    image = img.execute_transforms(images.PNG, 100)

    def trans():
        service_profile = get_service_profile(service_user)
        avatar = get_avatar_by_id(service_profile.avatarId)
        if not avatar:
            avatar = Avatar(user=service_profile.user)
        update_avatar_profile(service_profile, avatar, image)
        service_profile.version += 1
        service_profile.put()

        from rogerthat.bizz.job.update_friends import schedule_update_all_friends_of_service_user
        schedule_update_all_friends_of_service_user(service_profile)

    return run_in_transaction(trans, xg=True)


def update_avatar_profile(profile, avatar, image):
    avatar.picture = db.Blob(image)
    avatar.put()
    profile.avatarId = avatar.key().id()
    _calculateAndSetAvatarHash(profile, image)


@returns(unicode)
@arguments(user=users.User, app_id=unicode)
def get_profile_info_name(user, app_id):
    if user == MC_DASHBOARD:
        try:
            app_name = get_app_name_by_id(app_id)
        except:
            logging.debug('app_id:%s', app_id)
            raise
        if app_id == App.APP_ID_ROGERTHAT:
            return u"%s Dashboard" % app_name
        else:
            return app_name
    else:
        profile_info = get_profile_info(user)
        if profile_info:
            return profile_info.name or profile_info.qualifiedIdentifier or remove_slash_default(user).email()
        else:
            return user.email()


@returns(NoneType)
@arguments(profile_info=ProfileInfo, changed_properties=[unicode])
def update_friends(profile_info, changed_properties=None):
    """If profile_info is human user ==> update friends and services of human_user
    If profile_info is service_identity ==> update human friendMaps of service_identity"""
    from rogerthat.bizz.job.update_friends import schedule_update_friends_of_profile_info
    schedule_update_friends_of_profile_info(profile_info, changed_properties)


@returns([users.User])
@arguments(app_user=users.User, users_=[users.User])
def find_rogerthat_users_via_email(app_user, users_):
    users_ = filter(is_clean_app_user_email, users_)
    users_ = [p.user for p in get_existing_user_profiles(users_)]
    result = list()
    friend_map = get_friends_map(app_user)
    for u in users_:
        if u in friend_map.friends:
            continue
        result.append(u)
    return result


@returns([FacebookRogerthatProfileMatchTO])
@arguments(app_user=users.User, access_token=unicode)
def find_rogerthat_users_via_facebook(app_user, access_token):
    couple_facebook_id_with_profile(app_user, access_token)
    friends = get_friend_list_from_facebook(access_token)
    friends_dict = dict([(f['id'], (f['name'], f['picture']['data']['url'])) for f in friends])
    matches = get_existing_profiles_via_facebook_ids(friends_dict.keys(), get_app_id_from_app_user(app_user))
    result = list()
    friend_map = get_friends_map(app_user)
    for fbId, rtId in matches:
        if rtId in friend_map.friends:
            continue
        result.append(FacebookRogerthatProfileMatchTO(
            fbId, get_human_user_from_app_user(rtId).email(), friends_dict[fbId][0], friends_dict[fbId][1]))
    return result


def get_friend_list_from_facebook(access_token):
    args = dict()
    args["access_token"] = access_token
    args["fields"] = 'name,picture'
    result = urlfetch.fetch(url="https://graph.facebook.com/me/friends?" + urlencode(args), deadline=55)
    logging.info(result.content)
    if result.status_code == 200:
        return json.loads(result.content)["data"]
    raise Exception("Could not get friend list from facebook!\nstatus: %s\nerror:%s" %
                    (result.status_code, result.content))


def _calculateAndSetAvatarHash(profile, image):
    digester = hashlib.sha256()
    digester.update(image)
    profile.avatarHash = digester.hexdigest().upper()
    logging.info("New avatar hash: %s", profile.avatarHash)
    from rogerthat.pages.profile import get_avatar_cached
    invalidate_cache(get_avatar_cached, profile.avatarId, 50)
    invalidate_cache(get_avatar_cached, profile.avatarId, 67)
    invalidate_cache(get_avatar_cached, profile.avatarId, 100)
    invalidate_cache(get_avatar_cached, profile.avatarId, 150)


@returns(NoneType)
@arguments(user=users.User, user_profile=UserProfile, skipped_mobile=Mobile, countdown=(int, long))
def update_mobiles(user, user_profile, skipped_mobile=None, countdown=5):
    request = IdentityUpdateRequestTO()
    request.identity = get_identity(user, user_profile)
    deferred.defer(_update_mobiles_deferred, user, request, skipped_mobile, _transactional=db.is_in_transaction(),
                   _countdown=countdown)


def _update_mobiles_deferred(user, request, skipped_mobile):
    logging.info("Updating mobile of user %s" % user)
    extra_kwargs = dict()
    if skipped_mobile is not None:
        extra_kwargs[SKIP_ACCOUNTS] = [skipped_mobile.account]
    identityUpdate(identity_update_response_handler, logError, user, request=request, **extra_kwargs)


@returns(NoneType)
@arguments(service_user=users.User, app_user=users.User, data_string=unicode)
def set_profile_data(service_user, app_user, data_string):
    from rogerthat.bizz.service import InvalidJsonStringException, InvalidValueException, FriendNotFoundException

    data_object = None
    try:
        data_object = json.loads(data_string)
    except:
        raise InvalidJsonStringException()
    if data_object is None:
        raise InvalidJsonStringException()
    if not isinstance(data_object, dict):
        raise InvalidJsonStringException()

    for k, v in data_object.iteritems():
        if not isinstance(v, basestring):
            raise InvalidValueException(k, u"The values of profile_data must be strings")

    if not data_object:
        return

    def trans(data_update):
        user_profile = get_user_profile(app_user, cached=False)
        if not user_profile:
            logging.info('User %s not found', app_user.email())
            raise FriendNotFoundException()

        # Deserialize key-value store
        data = json.loads(user_profile.profileData) if user_profile.profileData else dict()

        # Update existing user data with new values
        data.update(data_update)

        # Remove keys with empty values
        for key in [key for key, value in data.iteritems() if value is None]:
            data.pop(key)

        user_profile.profileData = json.dumps(data) if data else None
        user_profile.put()

        on_trans_committed(update_mobiles, app_user, user_profile, countdown=0)
        on_trans_committed(schedule_re_index, app_user)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans, data_object)


def _archive_friend_connection(fsic_key):
    app_user = users.User(fsic_key.parent().name())
    service_identity_user = users.User(fsic_key.name())

    def trans():
        to_put = list()
        user_data_key = UserData.createKey(app_user, service_identity_user)
        fsic, user_data = db.get([fsic_key, user_data_key])
        if fsic:
            archived_fsic = fsic.archive(FriendServiceIdentityConnectionArchive)
            to_put.append(archived_fsic)
        if user_data:
            archived_user_data = user_data.archive(UserDataArchive)
            to_put.append(archived_user_data)
        if to_put:
            db.put(to_put)

    db.run_in_transaction(trans)
    breakFriendShip(service_identity_user, app_user)


def _unarchive_friend_connection(fsic_archive_key):
    app_user = users.User(fsic_archive_key.parent().name())
    service_identity_user = users.User(fsic_archive_key.name())

    user_data_key = UserDataArchive.createKey(app_user, service_identity_user)
    fsic_archive, user_data_archive = db.get([fsic_archive_key, user_data_key])

    to_delete = [fsic_archive]
    if user_data_archive:
        user_data_data = user_data_archive.data
        to_delete.append(user_data_archive)
    else:
        user_data_data = None

    # set disabled and enabled broadcast types
    def trans():
        fsic = get_friend_serviceidentity_connection(app_user, service_identity_user)
        fsic.disabled_broadcast_types = fsic_archive.disabled_broadcast_types
        fsic.enabled_broadcast_types = fsic_archive.enabled_broadcast_types
        fsic.put()
        db.delete(to_delete)

        deferred.defer(makeFriends, service_identity_user, app_user, app_user, None, None, notify_invitee=False,
                       notify_invitor=False, user_data=user_data_data, _countdown=2, _transactional=True)

    db.run_in_transaction(trans)


@returns()
@arguments(service_user=users.User)
def set_service_disabled(service_user):
    """
    Disconnects all connected users, stores them in an archive and deletes the service from search index.
    """
    from rogerthat.bizz.service import _cleanup_search_index, SERVICE_INDEX, SERVICE_LOCATION_INDEX
    from rogerthat.bizz.job.delete_service import remove_autoconnected_service
    from rogerthat.bizz.news import update_visibility_news_items

    def trans():
        to_put = list()
        service_profile = get_service_profile(service_user)
        service_profile.expiredAt = now()
        service_profile.enabled = False
        to_put.append(service_profile)
        service_identity_keys = get_service_identities_query(service_user, True)
        search_configs = db.get(
            [SearchConfig.create_key(create_service_identity_user(users.User(key.parent().name()), key.name())) for
             key in service_identity_keys])

        svc_index = search.Index(name=SERVICE_INDEX)
        loc_index = search.Index(name=SERVICE_LOCATION_INDEX)

        for search_config in search_configs:
            if search_config:
                old_search_enabled = search_config.enabled
                search_config.enabled = False
                to_put.append(search_config)
                on_trans_committed(_cleanup_search_index, search_config.service_identity_user.email(), svc_index,
                                   loc_index)
                on_trans_committed(cleanup_map_index, search_config.service_identity_user)
                if old_search_enabled != search_config.enabled:
                    on_trans_committed(update_visibility_news_items, search_config.service_identity_user, False)

        for objects_to_put in chunks(to_put, 200):
            put_and_invalidate_cache(*objects_to_put)

        deferred.defer(cleanup_sessions, service_user, _transactional=True)
        deferred.defer(cleanup_friend_connections, service_user, _transactional=True)
        deferred.defer(remove_autoconnected_service, service_user, _transactional=True)

    run_in_transaction(trans, True)


@returns()
@arguments(service_user=users.User)
def cleanup_friend_connections(service_user):
    run_job(get_all_service_friend_keys_query, [service_user], _archive_friend_connection, [])


@returns()
@arguments(service_user=users.User)
def cleanup_sessions(service_user):
    for user_profile_key in UserProfile.all(keys_only=True).filter('owningServiceEmails', service_user.email()):
        drop_sessions_of_user(users.User(user_profile_key.name()))
    drop_sessions_of_user(service_user)
    send_message(service_user, 'rogerthat.system.logout')


@returns()
@arguments(service_user=users.User)
def set_service_enabled(service_user):
    """
    Re-enables the service profile and restores all connected users.
    """
    service_profile = get_service_profile(service_user)
    service_profile.expiredAt = 0
    service_profile.enabled = True
    service_profile.put()

    run_job(get_all_archived_service_friend_keys_query, [service_user], _unarchive_friend_connection, [])
