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

from mcfw.properties import unicode_property, long_property, typed_property, bool_property, unicode_list_property, \
    long_list_property, azzert
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import ServiceTranslation, ServiceMenuDef, App
from rogerthat.models.properties.friend import BaseFriendDetail
from rogerthat.rpc import users
from rogerthat.to import TO
from rogerthat.translations import localize
from rogerthat.utils import merge_transfer_object
from rogerthat.utils.app import get_human_user_from_app_user, remove_app_id, get_app_id_from_app_user
from rogerthat.utils.service import remove_slash_default

FRIEND_TYPE_PERSON = BaseFriendDetail.TYPE_USER
FRIEND_TYPE_SERVICE = BaseFriendDetail.TYPE_SERVICE


class ServiceMenuItemLinkTO(object):
    url = unicode_property('0')
    external = bool_property('1', default=False)
    request_user_link = bool_property('2', default=False)


class FormVersionTO(TO):
    id = long_property('id')
    version = long_property('version')


class BaseServiceMenuItemTO(TO):
    coords = long_list_property('1')
    label = unicode_property('2')
    iconHash = unicode_property('3')
    screenBranding = unicode_property('4')
    staticFlowHash = unicode_property('5', default=None)
    requiresWifi = bool_property('7', default=False)
    runInBackground = bool_property('8', default=True)
    action = long_property('9', default=0)
    roles = long_list_property('10', default=[])
    link = typed_property('11', ServiceMenuItemLinkTO, False, default=None)
    fallThrough = bool_property('12', default=False)
    form = typed_property('13', FormVersionTO, default=None)
    embeddedApp = unicode_property('14', default=None)

    @classmethod
    def from_model(cls, helper, smd, language, static_flow_brandings, target_user_profile, existence=0,
                   calculate_icon_hash=True):
        translator = helper.get_translator()

        from rogerthat.bizz.service import calculate_icon_color_from_branding, get_menu_icon_hash
        smi = cls()
        smi.coords = smd.coords
        smi.label = translator.translate(ServiceTranslation.HOME_TEXT, smd.label, language)
        if calculate_icon_hash:
            if smd.iconHash:
                smi.iconHash = smd.iconHash
            else:
                icon_color = calculate_icon_color_from_branding(helper, target_user_profile)
                smi.iconHash = get_menu_icon_hash(smd.iconName, icon_color)
        else:
            smi.iconHash = None
        smi.screenBranding = translator.translate(ServiceTranslation.HOME_BRANDING, smd.screenBranding, language)
        smi.requiresWifi = smd.requiresWifi
        smi.runInBackground = smd.runInBackground
        smi.action = smd.action
        static_flow = None
        if smd.staticFlowKey:
            mfd = helper.get_message_flow(smd.staticFlowKey)
            static_flow = mfd.js_flow_definitions.get_by_language(language)
            if not static_flow:
                static_flow = mfd.js_flow_definitions.get_by_language(helper.get_service_profile().defaultLanguage)

        if static_flow:
            static_flow_brandings.extend(static_flow.brandings)
            smi.staticFlowHash = static_flow.hash_
        else:
            smi.staticFlowHash = None

        smi.roles = smd.roles

        if smd.link:
            smi.link = ServiceMenuItemLinkTO()
            smi.link.url = smd.link
            smi.link.external = smd.isExternalLink
            smi.link.request_user_link = smd.requestUserLink
        else:
            smi.link = None

        smi.fallThrough = smd.fallThrough or False
        smi.form = None if not smd.form_id else FormVersionTO(id=smd.form_id, version=smd.form_version)
        smi.embeddedApp = smd.embeddedApp
        return smi


class ServiceMenuItemTO(BaseServiceMenuItemTO):
    hashedTag = unicode_property('51', default=None)
    iconName = unicode_property('52', default=None)
    iconColor = unicode_property('53', default=None)

    @classmethod
    def from_model(cls, helper, smd, language, static_flow_brandings, target_user_profile, existence=0, **kwargs):
        """
        Args:
            smd (ServiceMenuDef)
            translator (function)
            language (unicode)
            static_flow_brandings (list of unicode)
            target_user_profile (rogerthat.models.UserProfile)
            service_identity_user (users.User)
            existence (int)
            **kwargs: keyword arguments
        Returns:
            ServiceMenuItemTO
        """
        smi = super(ServiceMenuItemTO, cls).from_model(helper, smd, language, static_flow_brandings,
                                                       target_user_profile, existence=existence)
        smi.hashedTag = smd.hashed_tag
        smi.iconName = smd.iconName if smd.iconName and smd.iconName.startswith('fa-') else None
        smi.iconColor = smd.iconColor
        return smi


class BaseServiceMenuTO(object):
    aboutLabel = unicode_property('2')
    messagesLabel = unicode_property('3')
    shareLabel = unicode_property('4')
    callLabel = unicode_property('5')
    callConfirmation = unicode_property('6')

    @classmethod
    def from_model(cls, helper, language):
        service_profile = helper.get_service_profile()
        service_identity = helper.get_profile_info()
        translator = helper.get_translator()
        actionMenu = cls()
        actionMenu.aboutLabel = translator.translate(
            ServiceTranslation.HOME_TEXT, service_profile.aboutMenuItemLabel, language)
        actionMenu.messagesLabel = translator.translate(
            ServiceTranslation.HOME_TEXT, service_profile.messagesMenuItemLabel, language)
        actionMenu.shareLabel = translator.translate(
            ServiceTranslation.HOME_TEXT, service_profile.shareMenuItemLabel, language)
        actionMenu.callLabel = translator.translate(
            ServiceTranslation.HOME_TEXT, service_profile.callMenuItemLabel, language)
        actionMenu.callConfirmation = translator.translate(
            ServiceTranslation.IDENTITY_TEXT, service_identity.callMenuItemConfirmation, language)
        return actionMenu


class ServiceMenuTO(BaseServiceMenuTO):
    branding = unicode_property('51')
    phoneNumber = unicode_property('52')
    share = bool_property('53')  # deprecated: always set to False
    items = typed_property('54', ServiceMenuItemTO, True)
    shareImageUrl = unicode_property('55')
    shareDescription = unicode_property('56')  # used in facebook wall post
    shareCaption = unicode_property('57')  # used in facebook wall post
    shareLinkUrl = unicode_property('58')  # used in facebook wall post
    staticFlowBrandings = unicode_list_property('59')

    @classmethod
    def from_model(cls, helper, language, target_user_profile, existence=0):
        actionMenu = super(ServiceMenuTO, cls).from_model(helper, language)
        actionMenu._populate(helper, language, target_user_profile, existence)
        return actionMenu

    def _populate(self, helper, language, target_user_profile, existence=0):
        from rogerthat.to.service import ServiceInteractionDefTO
        from rogerthat.bizz.service import get_service_interact_short_url
        translator = helper.get_translator()
        service_identity = helper.get_profile_info()

        self.branding = translator.translate(ServiceTranslation.HOME_BRANDING, service_identity.menuBranding, language)
        self.phoneNumber = translator.translate(
            ServiceTranslation.IDENTITY_TEXT, service_identity.mainPhoneNumber, language)
        if self.phoneNumber and self.phoneNumber.upper() == u'N/A':
            self.phoneNumber = None
        if service_identity.shareEnabled:
            sid = helper.get_share_sid()
            self.shareImageUrl = ServiceInteractionDefTO.urlFromServiceInteractionDef(sid)
            self.shareDescription = translator.translate(
                ServiceTranslation.IDENTITY_TEXT, service_identity.description, language)
            self.shareCaption = localize(language, "Scan QR code to discover!")
            self.shareLinkUrl = get_service_interact_short_url(sid) + "?email"
        else:
            self.shareImageUrl = None
            self.shareDescription = None
            self.shareCaption = None
            self.shareLinkUrl = None
        self.share = False  # For hiding this functionality on old clients

        self.staticFlowBrandings = list()
        self._populate_items(helper, translator, language, self.staticFlowBrandings, target_user_profile, existence)
        self.staticFlowBrandings = list(set(self.staticFlowBrandings))

    def _populate_items(self, helper, translator, language, staticFlowBrandings, target_user_profile, existence):
        has_role_cache = dict()

        def is_item_visible(smd):
            if not smd.roles:
                return True

            if not target_user_profile:
                return False

            from rogerthat.bizz.roles import has_role
            for role_id in sorted(smd.roles):
                user_has_role = has_role_cache.get(role_id)
                if user_has_role is None:
                    role = helper.get_role(role_id)
                    user_has_role = has_role_cache[role_id] = has_role(helper.get_profile_info(), target_user_profile,
                                                                       role)
                if user_has_role:
                    return True
            return False

        self.items = [ServiceMenuItemTO.from_model(helper, smd, language, staticFlowBrandings, target_user_profile,
                                                   existence)
                      for smd in filter(is_item_visible, helper.list_service_menu_items())]


class FriendTO(BaseFriendDetail):
    FLAG_FRIEND_NOT_REMOVABLE = 1

    avatarHash = unicode_property('100')
    description = unicode_property('101')
    descriptionBranding = unicode_property('102')
    pokeDescription = unicode_property('103')  # deprecated
    actionMenu = typed_property('104', ServiceMenuTO, False)
    generation = long_property('105')  # is in fact menuGeneration of service identity; unused for human friend
    qualifiedIdentifier = unicode_property('106', default=None)
    userData = unicode_property('107', default=None)  # deprecated
    appData = unicode_property('108', default=None)  # deprecated
    category_id = unicode_property('109', default=None)
    organizationType = long_property('111', default=0)
    callbacks = long_property('113', default=0)
    versions = long_list_property('114', default=[],
                                  doc="List of versions containing: "
                                      "(<serviceProfile.version>, )"  # in case of a service
                                      "<profileInfo.version>, <friendDetail.relationVersion>")
    flags = long_property('115', default=0)
    profileData = unicode_property('116', default=None)
    contentBrandingHash = unicode_property('117', default=None)
    homeBrandingHash = unicode_property('118', default=None)

    @staticmethod
    def fromDBFriendMap(helper, friendMap, friend, includeAvatarHash=False, includeServiceDetails=False,
                        targetUser=None):
        friend = remove_slash_default(friend)
        return FriendTO.fromDBFriendDetail(helper, friendMap.friendDetails[friend.email()], includeAvatarHash,
                                           includeServiceDetails, targetUser=targetUser)

    @staticmethod
    def fromDBFriendDetail(helper, friendDetail, includeAvatarHash=False, includeServiceDetails=False, targetUser=None,
                           existence=None):
        # type: (FriendHelper, FriendDetails, bool, bool, users.User, bool) -> FriendTO
        from rogerthat.bizz.communities.communities import get_community
        f = merge_transfer_object(friendDetail, FriendTO())
        user = users.User(friendDetail.email)

        if existence is None:
            existence = friendDetail.existence

        azzert(remove_slash_default(user) == user)

        profile_info = helper.get_profile_info()
        if friendDetail.type == FRIEND_TYPE_PERSON:
            f.email = get_human_user_from_app_user(user).email()

        if includeAvatarHash and profile_info:
            if helper.is_service:
                f.avatarHash = helper.get_service_profile().avatarHash
            else:
                # profile_info is a UserProfile here
                f.avatarHash = profile_info.avatarHash
        else:
            f.avatarHash = None

        f.pokeDescription = None  # deprecated

        if includeServiceDetails and friendDetail.type == FRIEND_TYPE_SERVICE:
            azzert(targetUser, "Can not decently translate FriendTO if targetUser is not supplied.")

            service_identity = profile_info
            azzert(service_identity)
            service_profile = helper.get_service_profile()

            f.flags = 0
            if targetUser:
                targetProfile = get_user_profile(targetUser)
                language = targetProfile.language
                community = get_community(targetProfile.community_id)
                if not community.is_service_removable(friendDetail.email):
                    f.flags |= FriendTO.FLAG_FRIEND_NOT_REMOVABLE
            else:
                targetProfile = None
                language = service_profile.defaultLanguage

            translator = helper.get_translator()
            f.generation = service_identity.menuGeneration or 0
            f.qualifiedIdentifier = translator.translate(
                ServiceTranslation.IDENTITY_TEXT, service_identity.qualifiedIdentifier, language)
            if targetUser and get_app_id_from_app_user(targetUser) == App.APP_ID_OSA_LOYALTY:
                f.description = None
                f.descriptionBranding = None
                f.actionMenu = None
                f.actions = []
            else:
                f.description = translator.translate(
                    ServiceTranslation.IDENTITY_TEXT, service_identity.description, language)
                f.descriptionBranding = translator.translate(
                    ServiceTranslation.IDENTITY_BRANDING, service_identity.descriptionBranding, language)
                f.actionMenu = ServiceMenuTO.from_model(helper, language, targetProfile, existence)
                f.actions = []

            f.userData = None
            f.appData = None
            f.category_id = service_profile.category_id
            f.organizationType = service_profile.organizationType
            f.existence = existence
            f.callbacks = service_profile.callbacks
            f.versions = [service_profile.version, service_identity.version, friendDetail.relationVersion]
            f.profileData = None
            f.contentBrandingHash = service_identity.contentBrandingHash
            f.homeBrandingHash = service_identity.homeBrandingHash
        else:
            f.description = None
            f.descriptionBranding = None
            f.actions = []
            f.actionMenu = None
            f.generation = 0
            f.qualifiedIdentifier = None
            f.userData = None
            f.appData = None
            f.category_id = None
            f.organizationType = 0
            f.existence = existence
            f.callbacks = 0
            if existence == FriendTO.FRIEND_EXISTENCE_DELETED:
                # profile_info might be None if the user's account is deactivated
                f.versions = []
                f.profileData = None
            else:
                if profile_info is None:
                    logging.error(
                        'profile_info is None. targetUser=%s, friendDetail=%s', targetUser, friendDetail.email)
                f.versions = [profile_info.version, friendDetail.relationVersion]
                f.profileData = None if profile_info.isServiceIdentity else profile_info.profileData
            f.flags = 0
            f.contentBrandingHash = None
            f.homeBrandingHash = None
        logging.debug('debugging_branding f.versions: %s', f.versions)
        return f


class FriendRelationTO(object):
    email = unicode_property('1')
    name = unicode_property('2')
    avatarId = long_property('3')
    type = long_property('4')  # @ReservedAssignment

    @staticmethod
    def fromDBFriendDetail(friendDetail):
        fr = FriendRelationTO()
        fr.email = remove_app_id(remove_slash_default(users.User(friendDetail.email), warn=True)).email()
        fr.name = friendDetail.name
        fr.avatarId = friendDetail.avatarId
        fr.type = friendDetail.type
        return fr


class FriendWithRelationsTO(object):
    friend = typed_property('1', FriendTO, False)
    friends = typed_property('2', FriendRelationTO, True)
    type = long_property('3')  # @ReservedAssignment


class FullFriendsInfoTO(object):
    shareContacts = bool_property('1')
    friends = typed_property('2', FriendWithRelationsTO, True)
    canShareLocation = bool_property('3')


class GetFriendsListRequestTO(object):
    pass


class GetFriendsListResponseTO(object):
    generation = long_property('1')
    friends = typed_property('2', FriendTO, True)


class GetFriendEmailsRequestTO(object):
    pass


class GetFriendEmailsResponseTO(object):
    generation = long_property('1')  # deprecated since 1.0.162.i and 1.0.1003.A
    emails = unicode_list_property('2')
    friend_set_version = long_property('3', default=0)


class GetFriendRequestTO(object):
    email = unicode_property('1')
    avatar_size = long_property('2')


class GetFriendResponseTO(object):
    generation = long_property('1')
    friend = typed_property('2', FriendTO, False)
    avatar = unicode_property('3')


class UpdateFriendRequestTO(object):
    STATUS_MODIFIED = 2
    STATUS_ADD = 1
    STATUS_DELETE = 0

    generation = long_property('1')  # deprecated since 1.0.162.i and 1.0.1003.A
    friend = typed_property('2', FriendTO, False)
    status = long_property('3')


class UpdateFriendResponseTO(object):
    updated = bool_property('1')
    reason = unicode_property('2', doc=u"Reason why client did not update the friendSet in it's local DB")


class UpdateFriendSetRequestTO(object):
    version = long_property('1')
    friends = unicode_list_property('2')
    added_friend = typed_property('3', FriendTO, False)  # for performance increase (preventing a getFriend request)


class UpdateFriendSetResponseTO(object):
    updated = bool_property('1')
    reason = unicode_property('2', doc=u"Reason why client did not update the friend in it's local DB")


class BecameFriendsRequestTO(object):
    user = unicode_property('1')
    friend = typed_property('2', FriendRelationTO, False)


class BecameFriendsResponseTO(object):
    pass


class ShareLocationRequestTO(object):
    friend = unicode_property('1')
    enabled = bool_property('2')


class ShareLocationResponseTO(object):
    pass


class RequestShareLocationRequestTO(object):
    friend = unicode_property('1')
    message = unicode_property('2')


class RequestShareLocationResponseTO(object):
    pass


class BreakFriendshipRequestTO(object):
    friend = unicode_property('1')


class BreakFriendshipResponseTO(object):
    pass


class InviteFriendRequestTO(object):
    email = unicode_property('1')
    message = unicode_property('2')
    allow_cross_app = bool_property('3', default=False)


class InviteFriendResponseTO(object):
    pass


class GetAvatarRequestTO(object):
    avatarId = long_property('1')
    size = long_property('2')


class GetAvatarResponseTO(object):
    avatar = unicode_property('1')


class GetUserInfoRequestTO(object):
    code = unicode_property('1')
    allow_cross_app = bool_property('2', default=False)


class ErrorTO(object):
    title = unicode_property('1', default=None, doc="The error title")
    message = unicode_property('2', default=None, doc="The error message")
    caption = unicode_property('3', default=None, doc="If not null, the caption of an extra button shown in the popup."
                                                      " Eg: Install the ... App")
    action = unicode_property('4', default=None, doc="If not null, the action (url) behind the button")


class GetUserInfoResponseTO(object):
    name = unicode_property('1')
    avatar = unicode_property('2')
    description = unicode_property('3')
    descriptionBranding = unicode_property('4')
    type = long_property('5')  # @ReservedAssignment
    email = unicode_property('6')
    qualifiedIdentifier = unicode_property('7')
    error = typed_property('8', ErrorTO, doc="", default=None)
    avatar_id = long_property('9', default=-1)
    profileData = unicode_property('10', default=None)
    app_id = unicode_property('11', default=None)


class ServiceFriendTO(object):
    email = unicode_property('1')
    name = unicode_property('2')
    avatar = unicode_property('3')
    language = unicode_property('4')
    app_id = unicode_property('5')
    app_name = unicode_property('6')


class FriendListResultTO(object):
    cursor = unicode_property('1')
    friends = typed_property('2', ServiceFriendTO, True)


class ServiceFriendStatusTO(ServiceFriendTO):
    is_friend = bool_property('101')
    last_heartbeat = long_property('102')
    devices = unicode_list_property('103')
    deactivated = bool_property('104')


class GetFriendInvitationSecretsRequestTO(object):
    pass


class GetFriendInvitationSecretsResponseTO(object):
    secrets = unicode_list_property('1')


class AckInvitationByInvitationSecretRequestTO(object):
    invitor_code = unicode_property('1')
    secret = unicode_property('2')


class AckInvitationByInvitationSecretResponseTO(object):
    pass


class LogInvitationSecretSentRequestTO(object):
    secret = unicode_property('1')
    phone_number = unicode_property('2')
    timestamp = long_property('3')


class LogInvitationSecretSentResponseTO(object):
    pass


class FindRogerthatUsersViaEmailRequestTO(object):
    email_addresses = unicode_list_property('1')


class FindRogerthatUsersViaEmailResponseTO(object):
    matched_addresses = unicode_list_property('1')


class FacebookRogerthatProfileMatchTO(object):
    fbId = unicode_property('1')
    rtId = unicode_property('2')
    fbName = unicode_property('3')
    fbPicture = unicode_property('4')

    def __init__(self, fbId, rtId, fbName, fbPicture):
        self.fbId = fbId
        self.rtId = rtId
        self.fbName = fbName
        self.fbPicture = fbPicture


class FindRogerthatUsersViaFacebookRequestTO(object):
    access_token = unicode_property('1')


class FindRogerthatUsersViaFacebookResponseTO(object):
    matches = typed_property('1', FacebookRogerthatProfileMatchTO, True)


class FriendCategoryTO(object):
    guid = unicode_property('1')
    name = unicode_property('2')
    avatar = unicode_property('3')

    @staticmethod
    def from_model(model):
        to = FriendCategoryTO()
        to.guid = model.id
        to.name = model.name
        to.avatar = unicode(base64.b64encode(str(model.avatar)))
        return to


class GetCategoryRequestTO(object):
    category_id = unicode_property('1')


class GetCategoryResponseTO(object):
    category = typed_property('1', FriendCategoryTO, False)


class GroupTO(object):
    guid = unicode_property('1')
    name = unicode_property('2')
    avatar_hash = unicode_property('3')
    members = unicode_list_property('4')

    @staticmethod
    def from_model(model):
        to = GroupTO()
        to.guid = model.guid
        to.name = model.name
        to.avatar_hash = model.avatar_hash
        to.members = []
        for m in model.members:
            to.members.append(get_human_user_from_app_user(users.User(m)).email())
        return to


class GetGroupsRequestTO(object):
    pass


class GetGroupsResponseTO(object):
    groups = typed_property('1', GroupTO, True)


class GetGroupAvatarRequestTO(object):
    avatar_hash = unicode_property('1')
    size = long_property('2')


class GetGroupAvatarResponseTO(object):
    avatar = unicode_property('1')


class PutGroupRequestTO(object):
    guid = unicode_property('1')
    name = unicode_property('2')
    avatar = unicode_property('3')
    members = unicode_list_property('4')


class PutGroupResponseTO(object):
    avatar_hash = unicode_property('1')


class DeleteGroupRequestTO(object):
    guid = unicode_property('1')


class DeleteGroupResponseTO(object):
    pass


class UpdateGroupsRequestTO(object):
    pass


class UpdateGroupsResponseTO(object):
    pass


class ServiceMenuDetailItemTO(BaseServiceMenuItemTO):
    tag = unicode_property('51', default=None)

    @classmethod
    def from_model(cls, helper, smd, language, static_flow_brandings, target_user_profile, existence=0, calculate_icon_hash=True):
        smi = super(ServiceMenuDetailItemTO, cls).from_model(helper, smd, language, static_flow_brandings,
                                                             target_user_profile, existence, calculate_icon_hash)
        smi.tag = smd.tag
        return smi


class ServiceMenuDetailTO(BaseServiceMenuTO):
    items = typed_property('51', ServiceMenuDetailItemTO, True)  # type: list[ServiceMenuDetailItemTO]

    @classmethod
    def from_model(cls, helper, calculate_icon_hash=True):
        service_profile = helper.get_service_profile()
        actionMenu = super(ServiceMenuDetailTO, cls).from_model(helper, service_profile.defaultLanguage)
        actionMenu.items = [ServiceMenuDetailItemTO.from_model(helper, smd, service_profile.defaultLanguage,
                                                               [], None, calculate_icon_hash)
                            for smd in helper.list_service_menu_items()]
        return actionMenu


class FindFriendRequestTO(object):
    search_string = unicode_property('1')
    cursor = unicode_property('2', default=None)
    avatar_size = long_property('3', default=50)


class FindFriendItemTO(object):
    email = unicode_property('1')
    name = unicode_property('2')
    avatar_url = unicode_property('3')


class FindFriendResponseTO(object):
    error_string = unicode_property('1')
    items = typed_property('2', FindFriendItemTO, True)
    cursor = unicode_property('3', default=None)


class UserScannedRequestTO(object):
    email = unicode_property('1')
    app_id = unicode_property('2')
    service_email = unicode_property('3')


class UserScannedResponseTO(object):
    pass


class RegistrationResultRolesTO(object):
    service = unicode_property('1')
    identity = unicode_property('2')
    ids = long_list_property('3')


class RegistrationUserInfoTO(object):
    name = unicode_property('name')
    avatar = unicode_property('avatar')  # base64 encoded


class RegistrationResultTO(object):
    result = unicode_property('1')
    auto_connected_services = unicode_list_property('2')
    roles = typed_property('3', RegistrationResultRolesTO, True)
    user_details = typed_property('4', RegistrationUserInfoTO, False)  # type: RegistrationUserInfoTO
