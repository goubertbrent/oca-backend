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

import hashlib
import itertools
import logging
from types import NoneType

from google.appengine.ext import db, deferred, ndb

from mcfw.rpc import returns, arguments
from rogerthat.bizz.job import run_job
from rogerthat.bizz.messaging import _send_deleted
from rogerthat.bizz.system import unregister_mobile
from rogerthat.dal import parent_key, put_and_invalidate_cache
from rogerthat.dal.friend import get_friends_map
from rogerthat.dal.location import delete_user_location
from rogerthat.dal.mobile import get_user_active_mobiles
from rogerthat.dal.profile import get_avatar_by_id, get_user_profile, get_all_facebook_profile_pointers, \
    get_profile_infos
from rogerthat.models import AuthorizedUser, Settings, MobileSettings, AvatarArchive, FriendMapArchive, UserData, \
    UserDataArchive, UserProfile, FacebookUserProfile, UserProfileArchive, FacebookUserProfileArchive, \
    DoNotSendMeMoreInvites, FacebookProfilePointer, ProfilePointer, UserAccount, FacebookProfilePointerArchive, \
    UserInvitationSecret, FriendMap, Avatar, Profile, UserInteraction, LocationMessage, ActivationLog, \
    UserProfileInfo
from rogerthat.rpc import users
from rogerthat.templates import get_languages_from_header
from rogerthat.utils import channel, now

AUTHORIZED = dict()


@returns(NoneType)
@arguments(user=users.User)
def cleanup(user):
    """
    Removes all traces in the datastore of a specific user.
    """
    user_keys = itertools.chain(*(db.Query(c, True).filter("user =", user) for c in (
        AuthorizedUser, Settings, MobileSettings)))
    db.delete(user_keys)
    for m in get_user_active_mobiles(user):
        unregister_mobile(user, m)
    db.delete(db.GqlQuery('SELECT __key__ WHERE ANCESTOR IS :1', parent_key(user)))


@returns(str)
@arguments(data=dict)
def calculate_secure_url_digest(data):
    digester = hashlib.sha256()
    digester.update(data["n"].encode('UTF8'))
    digester.update(data["e"].encode('UTF8'))
    digester.update(str(data["t"]))
    digester.update(data["a"].encode('UTF8'))
    if data["c"]:
        digester.update(data["c"].encode('UTF8'))
    return digester.hexdigest()


@returns(bool)
@arguments(app_user=users.User)
def unsubscribe_from_reminder_email(app_user):
    logging.info("unsubscribe_from_reminder_email user: %s", app_user)

    def trans():
        user_profile = get_user_profile(app_user)
        if not user_profile:
            logging.info("unsubscribe_from_reminder_email account that does not exists: %s", app_user)
            return False

        user_profile.unsubscribed_from_reminder_email = True
        put_and_invalidate_cache(user_profile)
        return True

    return db.run_in_transaction(trans)


@returns(NoneType)
@arguments(app_user=users.User, friend_map=FriendMap, user_profile=(UserProfile, FacebookUserProfile), hard_delete=bool,
           unregister_reason=unicode)
def archiveUserDataAfterDisconnect(app_user, friend_map, user_profile, hard_delete=False, unregister_reason=None):
    from rogerthat.bizz.friends import breakFriendShip
    from rogerthat.bizz.news.cleanup import job as cleanup_news
    from rogerthat.bizz.jobs.bizz import cleanup_jobs_data

    archives_to_put = list()
    models_to_delete = list()

    if isinstance(user_profile, FacebookUserProfile):
        logging.info("isinstance FacebookUserProfile")
        if not hard_delete:
            archives_to_put.append(user_profile.archive(FacebookUserProfileArchive))
    elif isinstance(user_profile, UserProfile):
        logging.info("isinstance UserProfile")
        if not hard_delete:
            archives_to_put.append(user_profile.archive(UserProfileArchive))
    else:
        logging.error("user_profile not an instance of UserProfile or FacebookUserPofile: %r", user_profile)

    for fpp in FacebookProfilePointer.all().filter("user =", app_user):
        if not hard_delete:
            archives_to_put.append(fpp.archive(FacebookProfilePointerArchive))
        models_to_delete.append(fpp)

    avatarId = -1 if not user_profile or not user_profile.avatarId else user_profile.avatarId
    if avatarId != -1:
        logging.info("avatar was set")
        avatar = get_avatar_by_id(avatarId)
        if avatar:
            if not hard_delete:
                archives_to_put.append(avatar.archive(AvatarArchive))
            models_to_delete.append(avatar)

    if friend_map:
        if not hard_delete:
            archives_to_put.append(friend_map.archive(FriendMapArchive))
        models_to_delete.append(friend_map)

        for userData in UserData.all().ancestor(parent_key(app_user)):
            if not hard_delete:
                archives_to_put.append(userData.archive(UserDataArchive))
            models_to_delete.append(userData)

        for f in friend_map.friendDetails:
            connected_user = users.User(f.email)
            breakFriendShip(friend_map.user, connected_user)

    for m in get_user_active_mobiles(app_user):
        unregister_mobile(app_user, m, unregister_reason)

    delete_user_location(app_user)

    dnsmmi = DoNotSendMeMoreInvites.get_by_key_name(app_user.email())
    if dnsmmi:
        models_to_delete.append(dnsmmi)

    if isinstance(user_profile, FacebookUserProfile):
        models_to_delete.extend(get_all_facebook_profile_pointers(app_user))

    pp = ProfilePointer.get_by_key_name(app_user.email())
    if pp:
        models_to_delete.append(pp)

    models_to_delete.append(UserAccount(parent=parent_key(app_user), key_name=app_user.email(), type="com.rogerthat"))
    models_to_delete.extend(UserInvitationSecret.all().ancestor(parent_key(app_user)).fetch(None))
    models_to_delete.append(user_profile)

    if hard_delete:
        delete_user_location_messages(app_user)
        models_to_delete.extend(UserInteraction.all().ancestor(parent_key(app_user)).fetch(None))

    logging.info("len(models_to_delete): %s %r", len(models_to_delete), models_to_delete)
    logging.info("len(archives_to_put): %s %r", len(archives_to_put), archives_to_put)

    if not hard_delete:
        db.put(archives_to_put)
    db.delete(models_to_delete)
    user_profile.invalidateCache()

    cleanup_news(app_user)
    cleanup_jobs_data(app_user)
    UserProfileInfo.create_key(app_user).delete()

    if hard_delete:
        from rogerthat.bizz.job import cleanup_user_messaging
        cleanup_user_messaging.job(app_user)


def delete_user_location_messages(app_user):
    run_job(_get_location_messages, [app_user], delete_location_message, [])


def _get_location_messages(app_user):
    return LocationMessage.list_by_user(app_user)


def delete_location_message(location_msg_key):
    location_msg = location_msg_key.get()  # type: LocationMessage
    _send_deleted(users.User(location_msg.receiver), location_msg.message_id)
    ndb.delete_multi([location_msg_key, location_msg.message_key])


@returns(NoneType)
@arguments(profile=(UserProfileArchive, FacebookUserProfileArchive), app_user=users.User, owncloud_password=unicode,
           tos_version=(int, long, NoneType), consent_push_notifications_shown=bool)
def reactivate_user_profile(profile, app_user, owncloud_password=None, tos_version=None,
                            consent_push_notifications_shown=False):

    def trans():

        models_to_restore = list()
        archives_to_delete = list()

        archives_to_delete.append(profile)
        if isinstance(profile, UserProfileArchive):
            new_user_profile = profile.archive(UserProfile)
        else:
            new_user_profile = profile.archive(FacebookUserProfile)
        models_to_restore.append(new_user_profile)

        if owncloud_password and not new_user_profile.owncloud_password:
            new_user_profile.owncloud_password = owncloud_password
        if tos_version:
            new_user_profile.tos_version = tos_version
        if consent_push_notifications_shown:
            new_user_profile.consent_push_notifications_shown = True
        new_user_profile.invalidateCache()

        db.put(models_to_restore)
        db.delete(archives_to_delete)
        deferred.defer(restoreUserDataAfterReactivate, app_user, _transactional=True)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


def restoreUserDataAfterReactivate(app_user):
    models_to_restore = list()
    archives_to_delete = list()

    for avatar_archive in AvatarArchive.all().filter("user =", app_user):
        archives_to_delete.append(avatar_archive)
        models_to_restore.append(avatar_archive.archive(Avatar))

    friend_map_archive = FriendMapArchive.get_by_key_name(app_user.email(), parent_key(app_user))
    if friend_map_archive:
        archives_to_delete.append(friend_map_archive)
        friend_map = friend_map_archive.archive(FriendMap)
        models_to_restore.append(friend_map)

    for user_data_archive in UserDataArchive.all().ancestor(parent_key(app_user)):
        archives_to_delete.append(user_data_archive)
        models_to_restore.append(user_data_archive.archive(UserData))

    for fb_pp_archive in FacebookProfilePointerArchive.all().filter("user =", app_user):
        archives_to_delete.append(fb_pp_archive)
        models_to_restore.append(fb_pp_archive.archive(FacebookProfilePointer))

    logging.info("len(models_to_restore) %s %r", len(models_to_restore), models_to_restore)
    logging.info("len(archives_to_delete) %s %r", len(archives_to_delete), archives_to_delete)
    db.put(models_to_restore)
    db.delete(archives_to_delete)

    if not AuthorizedUser.all().filter(u"user =", app_user).get():
        au = AuthorizedUser()
        au.user = app_user
        au.put()

    if friend_map_archive:
        from rogerthat.bizz.friends import makeFriends

        # Skip friends that unsubscribed in the meantime
        cleanup_friend_map = False
        friend_profile_infos = get_profile_infos(friend_map.friends, allow_none_in_results=True)

        for friend_user, friendProfileInfo in zip(friend_map.friends, friend_profile_infos):
            if friendProfileInfo:
                continue
            logging.debug('User %s must have been deactivated in the mean while. Not executing makeFriends.',
                          friend_user.email())
            friend_map.friends.remove(friend_user)
            friend_map.friendDetails.remove(friend_user.email())
            cleanup_friend_map = True
        if cleanup_friend_map:
            friend_map.put()

        # MakeFriends of remaining users in friendMap
        for f in friend_map.friendDetails:
            connected_user = users.User(f.email)
            makeFriends(friend_map.user, connected_user, connected_user, servicetag=None, origin=None,
                        notify_invitee=False, notify_invitor=False, user_data=None)


@returns(NoneType)
@arguments(profile=Profile, request_headers=object)
def update_user_profile_language_from_headers(profile, request_headers):
    if isinstance(profile, UserProfile) and not profile.language:
        language_header = request_headers.get('Accept-Language', None)
        language = get_languages_from_header(language_header)[0] if language_header else None
        if language:

            def update():
                p = db.get(profile.key())
                if not p.language:
                    p.language = language
                    p.put()

            db.run_in_transaction(update)


@returns(NoneType)
@arguments(app_user=users.User)
def delete_account(app_user):
    logging.info("delete_account user: %s", app_user)

    def trans():
        user_profile = get_user_profile(app_user)
        if not user_profile:
            logging.info("delete account that does not exists: %s", app_user)
            return

        friend_map = get_friends_map(app_user)

        users.clear_user()
        channel.send_message(app_user, u'rogerthat.system.dologout')

        deferred.defer(archiveUserDataAfterDisconnect, app_user, friend_map, user_profile, True, _transactional=True)
        ActivationLog(timestamp=now(), email=app_user.email(),
                      description='Delete account | %s' % app_user).put()

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


@returns(unicode)
@arguments(app_user=users.User)
def get_lang(app_user):
    """
    Gets the users' language from his user profile
    Args:
        app_user (users.User)
    Returns:
        unicode
    """
    return get_user_profile(app_user).language
