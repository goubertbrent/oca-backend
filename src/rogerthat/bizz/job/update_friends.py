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

import logging
from types import NoneType

from google.appengine.ext import db, deferred
from typing import List

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.features import Features, all_mobiles_support_feature
from rogerthat.bizz.friend_helper import FriendHelper
from rogerthat.bizz.friends import update_friend_response, update_friend_set_response, \
    friend_update_response_receiver
from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.capi.friends import updateFriend, updateFriendSet
from rogerthat.consts import DEFAULT_QUEUE, HIGH_LOAD_WORKER_QUEUE, \
    SCHEDULED_QUEUE
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.friend import get_friends_friends_maps_keys_query, get_friends_map_key_by_user
from rogerthat.dal.mobile import get_mobile_key_by_account
from rogerthat.dal.profile import get_user_profile, get_service_profile, get_service_profiles
from rogerthat.dal.service import get_friend_service_identity_connections_keys_of_app_user_query, \
    get_service_identities_query, get_one_friend_service_identity_connection_keys_query
from rogerthat.models import ProfileInfo, ServiceTranslation, FriendMap, ServiceProfile, UserProfile, UserData
from rogerthat.models.properties.friend import FriendDetailTO
from rogerthat.rpc import users
from rogerthat.rpc.models import RpcCAPICall
from rogerthat.rpc.rpc import logError
from rogerthat.rpc.service import logServiceError
from rogerthat.to.friends import UpdateFriendRequestTO, FriendTO, UpdateFriendSetRequestTO, FRIEND_TYPE_SERVICE
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import channel, get_current_queue
from rogerthat.utils.app import remove_app_id
from rogerthat.utils.service import remove_slash_default, get_service_user_from_service_identity_user, \
    create_service_identity_user
from rogerthat.utils.transactions import run_in_transaction

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO  # @UnusedImport


def _determine_worker_queue():
    current_queue = get_current_queue()
    return HIGH_LOAD_WORKER_QUEUE if current_queue in (None, DEFAULT_QUEUE, SCHEDULED_QUEUE) else current_queue


def _must_continue_with_update_service(service_profile_or_user, bump_service_version=False):
    def trans(service_profile):
        azzert(service_profile)
        service_profile_updated = False
        if not service_profile.autoUpdating and not service_profile.updatesPending:
            service_profile.updatesPending = True
            service_profile_updated = True
        if bump_service_version:
            service_profile.version += 1
            service_profile_updated = True

        if service_profile_updated:
            channel.send_message(service_profile.user, 'rogerthat.service.updatesPendingChanged',
                                 updatesPending=service_profile.updatesPending)
            service_profile.put()

        return service_profile.autoUpdating

    is_user = not isinstance(service_profile_or_user, ServiceProfile)
    if db.is_in_transaction():
        azzert(not is_user)
        service_profile = service_profile_or_user
        auto_updating = trans(service_profile_or_user)
    else:
        service_profile = get_service_profile(service_profile_or_user, False) if is_user else service_profile_or_user
        auto_updating = db.run_in_transaction(trans, service_profile)

    if not auto_updating:
        logging.info("Auto-updates for %s are suspended." % service_profile.user.email())
    return auto_updating


@returns(NoneType)
@arguments(profile_info=ProfileInfo, changed_properties=[unicode])
def schedule_update_friends_of_profile_info(profile_info, changed_properties=None):
    """If profile_info is human user ==> update friends and services of human_user
    If profile_info is service_identity ==> update human friendMaps of service_identity"""
    if profile_info.isServiceIdentity:
        service_profile = get_service_profile(profile_info.service_user)
        if not _must_continue_with_update_service(service_profile):
            return

    worker_queue = _determine_worker_queue()
    friend_type = FriendTO.TYPE_SERVICE if profile_info.isServiceIdentity else FriendTO.TYPE_USER
    deferred.defer(_run_update_friends_by_profile_info, profile_info.user, friend_type, changed_properties,
                   worker_queue=worker_queue,
                   _transactional=db.is_in_transaction(),
                   _queue=worker_queue)


@returns(NoneType)
@arguments(service_profile_or_user=(ServiceProfile, users.User), force=bool, bump_service_version=bool)
def schedule_update_all_friends_of_service_user(service_profile_or_user, force=False, bump_service_version=False):
    """Schedule update of all service_identities of a service to all connected users"""
    is_user = not isinstance(service_profile_or_user, ServiceProfile)
    service_user = service_profile_or_user if is_user else service_profile_or_user.user
    azzert('/' not in service_user.email(), "Expecting a service user, not a service identity.")
    if not force and not _must_continue_with_update_service(service_profile_or_user, bump_service_version):
        return
    worker_queue = _determine_worker_queue()
    deferred.defer(_run_update_all_friends_of_service_user, service_user,
                   worker_queue=worker_queue,
                   _transactional=db.is_in_transaction(),
                   _queue=worker_queue)


@returns(NoneType)
@arguments(service_profile_or_user=(ServiceProfile, users.User), target_user=users.User, force=bool)
def schedule_update_a_friend_of_service_user(service_profile_or_user, target_user, force=False):
    '''Schedule update of all service_identities of a service to 1 user'''
    is_user = not isinstance(service_profile_or_user, ServiceProfile)
    service_user = service_profile_or_user if is_user else service_profile_or_user.user
    azzert('/' not in service_user.email(), "Expecting a service user, not a service identity.")
    if not force and not _must_continue_with_update_service(service_profile_or_user, False):
        return
    deferred.defer(_run_update_friend_for_service_identities, service_user, target_user,
                   _transactional=db.is_in_transaction())


@returns(NoneType)
@arguments(service_identity_user=users.User, target_user=users.User, force=bool)
def schedule_update_a_friend_of_a_service_identity_user(service_identity_user, target_user, force=False):
    """Schedule update of 1 service_identity to 1 user"""
    azzert('/' in service_identity_user.email(), "Expecting a service identity user.")
    service_user = get_service_user_from_service_identity_user(service_identity_user)
    if db.is_in_transaction():
        service_profile_or_service_user = get_service_profile(service_user, False)
    else:
        service_profile_or_service_user = service_user
    if not force and not _must_continue_with_update_service(service_profile_or_service_user, False):
        return
    deferred.defer(_serialize_and_update_friend_for_service_identity, service_identity_user,
                   get_one_friend_service_identity_connection_keys_query, [service_identity_user, target_user],
                   _transactional=db.is_in_transaction())


def _run_update_all_friends_of_service_user(service_user, worker_queue=HIGH_LOAD_WORKER_QUEUE):
    for si_key in get_service_identities_query(service_user, keys_only=True):
        si_user = create_service_identity_user(users.User(si_key.parent().name()), si_key.name())
        deferred.defer(_run_update_friends_by_profile_info, si_user, FRIEND_TYPE_SERVICE, None,
                       worker_queue, _queue=worker_queue)


def _run_update_friend_for_service_identities(service_user, target_user,
                                              worker_queue=HIGH_LOAD_WORKER_QUEUE):
    for si_key in get_service_identities_query(service_user, keys_only=True):
        si_user = create_service_identity_user(users.User(si_key.parent().name()), si_key.name())
        deferred.defer(_serialize_and_update_friend_for_service_identity, si_user,
                       get_one_friend_service_identity_connection_keys_query, [si_user, target_user],
                       worker_queue=worker_queue)


def _serialize_and_update_friend_for_service_identity(service_identity_user, get_fsics_query_function,
                                                      get_fsics_query_function_args,
                                                      worker_queue=HIGH_LOAD_WORKER_QUEUE):
    helper = FriendHelper.serialize(service_identity_user, FRIEND_TYPE_SERVICE)

    run_job(get_fsics_query_function, get_fsics_query_function_args, _update_friend_via_friend_connection,
            [helper],
            worker_queue=worker_queue)


def _run_update_friends_by_profile_info(user, friend_type, changed_properties, worker_queue=HIGH_LOAD_WORKER_QUEUE):
    def trans(user):
        helper = FriendHelper.serialize(user, friend_type)

        if friend_type == FRIEND_TYPE_SERVICE:
            user = remove_slash_default(user)
        else:
            update_friend_service_identity_connections(UserProfile.createKey(user), changed_properties)

        run_job(get_friends_friends_maps_keys_query, [user], _update_friend, [helper],
                worker_queue=worker_queue)

    run_in_transaction(trans, True, user)


def update_friend_service_identity_connections(profile_info_key, changed_properties):
    user = users.User(profile_info_key.parent().name())
    run_job(get_friend_service_identity_connections_keys_of_app_user_query, [user],
            _update_service_friends, [profile_info_key, changed_properties],
            MODE_BATCH, batch_timeout=2)


def _update_friend_via_friend_connection(friend_connection_key, helper):
    fsic = db.get(friend_connection_key)
    if not fsic or fsic.deleted:
        return
    _update_friend(get_friends_map_key_by_user(fsic.friend), helper)


def _update_friend(friend_map_key, helper):
    # type: (db.Key, FriendHelper) -> None
    profile_info = helper.get_profile_info()
    if profile_info.isServiceIdentity:
        service_profile = helper.get_service_profile()
        avatar_id = service_profile.avatarId
        translator = helper.get_translator()
    else:
        avatar_id = profile_info.avatarId

    def trans():
        # type: () -> None
        friend_map = FriendMap.get(friend_map_key)  # type: FriendMap
        if not friend_map:
            logging.warn("FriendMap not found for key: %s" % friend_map_key)
            return

        email = remove_slash_default(profile_info.user).email()
        friend_details = friend_map.get_friend_details()
        if email not in friend_details:
            logging.warn(friend_details.keys())
            logging.warn("Probably friend %s was removed while updating %s" % (email, friend_map.user.email()))
            return

        friend_detail = friend_details[email]
        friend_detail.avatarId = avatar_id
        if profile_info.isServiceIdentity:
            target_user_profile = get_user_profile(friend_map.user)
            if not target_user_profile:
                logging.warn("UserProfile not found for user: %s" % friend_map.user)
                return
            target_language = target_user_profile.language
            friend_detail.name = translator.translate(ServiceTranslation.IDENTITY_TEXT, profile_info.name,
                                                      target_language)
        else:
            friend_detail.name = profile_info.name
        friend_detail.type = helper.friend_type
        friend_detail.relationVersion += 1
        friend_map.save_friend_details(friend_details)
        friend_map.generation += 1

        to_put = [friend_map]

        logging.info("updating friend to friend_map.generation: %s, friend_detail.relationVersion: %s",
                     friend_map.generation, friend_detail.relationVersion)

        to_put.extend(create_update_friend_requests(helper, helper.profile_info_user, friend_map,
                                                    UpdateFriendRequestTO.STATUS_MODIFIED))
        put_and_invalidate_cache(*to_put)

    run_in_transaction(trans, True)


@returns([RpcCAPICall])
@arguments(helper=FriendHelper, updated_user=users.User, friend_map=FriendMap, status=int, extra_conversion_kwargs=dict,
           skip_mobiles=[unicode])
def create_update_friend_requests(helper, updated_user, friend_map, status, extra_conversion_kwargs=None,
                                  skip_mobiles=None):
    """
    Sends the correct request (UpdateFriendRequest or UpdateFriendSetRequest) to the client,
    based on the version of the mobile.

    Args:
        helper(FriendHelper):
        updated_user(users.User): The user which has been updated.
        friend_map(FriendMap): Friend map of the target user
        status(int): The kind of friend update. See UpdateFriendRequestTO.STATUS_*
        extra_conversion_kwargs(dict): Optional kwargs to pass to the FriendTO.fromDBFriendDetail method.
        skip_mobiles([unicode]): mobile accounts that should be skipped.
    Returns:
        list[RpcCAPICall]
    """
    azzert(status in (UpdateFriendRequestTO.STATUS_ADD,
                      UpdateFriendRequestTO.STATUS_DELETE,
                      UpdateFriendRequestTO.STATUS_MODIFIED))
    target_user = friend_map.user

    if status == UpdateFriendRequestTO.STATUS_DELETE:
        friend_detail = None
    else:
        friend_detail = friend_map.get_friend_detail_by_email(remove_slash_default(updated_user).email())
        if not friend_detail:
            logging.warn("%s not found in the friendMap of %s. Not sending updateFriend request with status=%s",
                         remove_slash_default(updated_user), target_user, status)
    if not friend_detail:
        return []
    friend_to = convert_friend(helper, target_user, friend_detail, status, extra_conversion_kwargs)

    capi_calls = do_update_friend_request(target_user, friend_to, status, friend_map, helper, skip_mobiles)
    if friend_to and helper.is_service:
        channel.send_message(target_user, u'rogerthat.friends.update', friend=friend_to.to_dict())
    return capi_calls


@returns(FriendTO)
@arguments(helper=FriendHelper, target_user=users.User, updated_friend_detail=FriendDetailTO, status=(int, long),
           extra_conversion_kwargs=dict)
def convert_friend(helper, target_user, updated_friend_detail, status, extra_conversion_kwargs=None):
    # type: (FriendHelper, users.User, FriendDetail, long, dict) -> FriendTO
    conversion_kwargs = {
        'includeAvatarHash': True,
        'includeServiceDetails': status != UpdateFriendRequestTO.STATUS_DELETE,
        'targetUser': target_user
    }
    if extra_conversion_kwargs:
        conversion_kwargs.update(extra_conversion_kwargs)

    logging.debug('Running FriendTO.fromDBFriendDetail for %s with the following kwargs: %s',
                  updated_friend_detail.email, conversion_kwargs)
    return FriendTO.fromDBFriendDetail(helper, updated_friend_detail, **conversion_kwargs)


@returns([RpcCAPICall])
@arguments(target_user=users.User, friend=FriendTO, status=int, friend_map=FriendMap, helper=FriendHelper,
           skip_mobiles=[unicode])
def do_update_friend_request(target_user, friend, status, friend_map, helper, skip_mobiles=None):
    # type: (users.User, FriendTO, int, FriendMap, FriendHelper, List[unicode]) -> List[RpcCAPICall]
    user_profile = get_user_profile(target_user)
    service_identity_user = helper.service_identity_user
    mobile_details = user_profile.get_mobiles().values() or []
    models = db.get([UserData.createKey(target_user, service_identity_user)] + [
        get_mobile_key_by_account(mobile_detail.account) for mobile_detail in mobile_details])
    user_data, mobiles = models[0], models[1:]

    def update_friend_set():
        # type: () -> List[RpcCAPICall]
        capi_calls = []
        request = UpdateFriendSetRequestTO()
        request.friends = [remove_app_id(users.User(f.email)).email() for f in friend_map.get_friend_details().values()]
        request.version = friend_map.version
        logging.debug('debugging_branding do_update_friend_request friend_map.ver %s', friend_map.version)
        request.added_friend = None
        if status == UpdateFriendRequestTO.STATUS_ADD:
            request.added_friend = friend

        for mobile in mobiles:
            capi_calls.extend(updateFriendSet(update_friend_set_response, logError, target_user, request=request,
                                              MOBILE_ACCOUNT=mobile, SKIP_ACCOUNTS=skip_mobiles,
                                              DO_NOT_SAVE_RPCCALL_OBJECTS=True))

        if status == UpdateFriendRequestTO.STATUS_ADD and friend.type == FriendTO.TYPE_SERVICE:
            from rogerthat.bizz.service import create_send_user_data_requests, create_send_app_data_requests
            capi_calls.extend(create_send_user_data_requests(mobiles, user_data, target_user, service_identity_user))
            capi_calls.extend(create_send_app_data_requests(mobiles, target_user, helper))

        return capi_calls

    def update_friend():
        # type: () -> List[RpcCAPICall]
        request = UpdateFriendRequestTO()
        request.friend = friend
        request.generation = friend_map.generation  # deprecated
        logging.debug('debugging_branding do_update_friend_request friend_map.gen %s', friend_map.generation)
        request.status = status

        capi_calls = []
        for mobile in mobiles:
            capi_calls.extend(updateFriend(update_friend_response, logError, target_user, request=request,
                                           DO_NOT_SAVE_RPCCALL_OBJECTS=True, MOBILE_ACCOUNT=mobile,
                                           SKIP_ACCOUNTS=skip_mobiles))
        for capi_call in capi_calls:
            capi_call.update_status = status

        if friend.type == FriendTO.TYPE_SERVICE:
            from rogerthat.bizz.service import create_send_user_data_requests, create_send_app_data_requests
            if not all_mobiles_support_feature(mobiles, Features.SPLIT_USER_DATA):
                capi_calls.extend(create_send_user_data_requests(mobiles, user_data, target_user,
                                                                 service_identity_user))
            capi_calls.extend(create_send_app_data_requests(mobiles, target_user, helper))

        return capi_calls

    status_is_added_or_removed = status in (UpdateFriendRequestTO.STATUS_ADD, UpdateFriendRequestTO.STATUS_DELETE)
    # Recent mobiles expect an UpdateFriendSetRequest when a friend is added or removed
    if status_is_added_or_removed:
        return update_friend_set()
    else:
        return update_friend()


def _update_service_friends(friend_service_identity_connection_keys, user_profile_key, changed_properties):
    # type: (list[db.Key], db.Key, list[unicode]) -> None
    from rogerthat.service.api import friends
    changed_properties = changed_properties or []

    def trans():
        models = db.get([user_profile_key] + friend_service_identity_connection_keys)  # type: list
        user_profile = models.pop(0)  # type: UserProfile
        assert isinstance(user_profile, UserProfile)
        friend_service_identity_connections = []  # type: List[FriendServiceIdentityConnection]
        for fsic in models:  # type: FriendServiceIdentityConnection
            if not fsic:
                continue
            fsic.friend_name = user_profile.name
            fsic.friend_avatarId = user_profile.avatarId
            friend_service_identity_connections.append(fsic)
        if friend_service_identity_connections:
            db.put(friend_service_identity_connections)
        return user_profile, friend_service_identity_connections

    user_profile, fsics = db.run_in_transaction(trans)
    user_details = UserDetailsTO.fromUserProfile(user_profile)

    service_api_callbacks = []
    service_users = {get_service_user_from_service_identity_user(fsic.service_identity_user) for fsic in fsics}
    for service_profile in get_service_profiles(list(service_users)):
        context = friends.update(friend_update_response_receiver, logServiceError, service_profile,
                                 user_details=user_details, changed_properties=changed_properties,
                                 DO_NOT_SAVE_RPCCALL_OBJECTS=True)
        if context:
            service_api_callbacks.append(context)
    logging.info('sending friend.update to %s/%s services', len(service_api_callbacks), len(service_users))
    db.put(service_api_callbacks)
