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
from rogerthat.models import Settings, MobileSettings, UserData, UserProfile, FacebookUserProfile, \
    DoNotSendMeMoreInvites, FacebookProfilePointer, ProfilePointer, \
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
    user_keys = itertools.chain(*(db.Query(c, True).filter("user =", user) for c in (Settings, MobileSettings)))
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
@arguments(app_user=users.User, friend_map=FriendMap, user_profile=(UserProfile, FacebookUserProfile), unregister_reason=unicode)
def delete_user_data(app_user, friend_map, user_profile, unregister_reason=None):
    from rogerthat.bizz.friends import breakFriendShip
    from rogerthat.bizz.news.cleanup import job as cleanup_news
    from rogerthat.bizz.jobs.workers import cleanup_jobs_data
    from rogerthat.bizz.job import cleanup_user_messaging

    models_to_delete = list()

    if isinstance(user_profile, FacebookUserProfile):
        logging.info("isinstance FacebookUserProfile")
    elif isinstance(user_profile, UserProfile):
        logging.info("isinstance UserProfile")
    else:
        logging.error("user_profile not an instance of UserProfile or FacebookUserPofile: %r", user_profile)

    for fpp in FacebookProfilePointer.all().filter("user =", app_user):
        models_to_delete.append(fpp)

    avatarId = -1 if not user_profile or not user_profile.avatarId else user_profile.avatarId
    if avatarId != -1:
        logging.info("avatar was set")
        avatar = get_avatar_by_id(avatarId)
        if avatar:
            models_to_delete.append(avatar)

    if friend_map:
        models_to_delete.append(friend_map)

        for userData in UserData.all().ancestor(parent_key(app_user)):
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

    models_to_delete.extend(UserInvitationSecret.all().ancestor(parent_key(app_user)).fetch(None))
    models_to_delete.append(user_profile)

    delete_user_location_messages(app_user)
    models_to_delete.extend(UserInteraction.all().ancestor(parent_key(app_user)).fetch(None))

    logging.info("len(models_to_delete): %s %r", len(models_to_delete), models_to_delete)

    cleanup_news(app_user)
    cleanup_jobs_data(app_user)
    UserProfileInfo.create_key(app_user).delete()

    db.delete(models_to_delete)
    user_profile.invalidateCache()
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

        deferred.defer(delete_user_data, app_user, friend_map, user_profile, _transactional=True)
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
