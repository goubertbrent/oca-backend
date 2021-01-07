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

from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.service import poke_service, poke_service_by_hashed_tag, render_menu_icon, get_menu_icon, \
    fake_friend_connection, get_user_link
from rogerthat.dal.app import get_app_name_by_id, get_app_by_id
from rogerthat.dal.service import get_service_identity, get_friend_serviceidentity_connection
from rogerthat.models import ProfilePointer, ServiceTranslation, MessageFlowDesign, ServiceProfile, ServiceIdentity
from rogerthat.models.properties.friend import FriendDetail
from rogerthat.rpc.rpc import expose
from rogerthat.to.friends import ErrorTO
from rogerthat.to.service import GetServiceActionInfoResponseTO, GetServiceActionInfoRequestTO, \
    StartServiceActionResponseTO, StartServiceActionRequestTO, GetMenuIconRequestTO, GetMenuIconResponseTO, \
    PressMenuIconResponseTO, PressMenuIconRequestTO, ShareServiceResponseTO, ShareServiceRequestTO, \
    FindServiceResponseTO, FindServiceRequestTO, PokeServiceResponseTO, PokeServiceRequestTO, GetStaticFlowResponseTO, \
    GetStaticFlowRequestTO, SendApiCallResponseTO, SendApiCallRequestTO, UpdateUserDataResponseTO, \
    UpdateUserDataRequestTO, GetUserLinkResponseTO, GetUserLinkRequestTO
from rogerthat.translations import localize
from rogerthat.utils import slog
from rogerthat.utils.app import create_app_user, get_app_id_from_app_user
from rogerthat.utils.service import create_service_identity_user, add_slash_default, remove_slash_default


@expose(('api',))
@returns(GetServiceActionInfoResponseTO)
@arguments(request=GetServiceActionInfoRequestTO)
def getActionInfo(request):
    from rogerthat.bizz import log_analysis
    from rogerthat.bizz.i18n import get_translator
    from rogerthat.dal.profile import get_user_profile, get_service_profile
    from rogerthat.dal.service import get_service_interaction_def
    from rogerthat.pages.profile import get_avatar
    from rogerthat.rpc import users
    pp = ProfilePointer.get(request.code)
    azzert(pp, "User with userCode %s not found!" % request.code)
    sid = request.action
    if sid and "?" in sid:
        sid = sid[:sid.index("?")]
    sid = get_service_interaction_def(pp.user, int(sid))
    azzert(sid, "Service interaction definition with id %s for service %s not found!" %
           (request.action, pp.user.email()))
    si = get_service_identity(create_service_identity_user(pp.user, sid.service_identity or ServiceIdentity.DEFAULT))
    app_user = users.get_current_user()
    target_language = get_user_profile(app_user).language
    translator = get_translator(si.service_user, ServiceTranslation.IDENTITY_TYPES, target_language)

    response = GetServiceActionInfoResponseTO()
    response.name = translator.translate(ServiceTranslation.IDENTITY_TEXT, si.name, target_language)
    response.email = remove_slash_default(si.user).email()
    response.qualifiedIdentifier = translator.translate(
        ServiceTranslation.IDENTITY_TEXT, si.qualifiedIdentifier, target_language)
    response.avatar = unicode(base64.b64encode(get_avatar(si.avatarId)))
    response.avatar_id = si.avatarId
    response.description = translator.translate(ServiceTranslation.IDENTITY_TEXT, si.description, target_language)
    response.descriptionBranding = sid.branding or translator.translate(
        ServiceTranslation.IDENTITY_BRANDING, si.descriptionBranding, target_language)
    response.type = FriendDetail.TYPE_SERVICE
    response.actionDescription = sid.description
    response.profileData = None
    response.app_id = None
    static_flow = None
    if sid.staticFlowKey:
        mfd = MessageFlowDesign.get(sid.staticFlowKey)
        static_flow = mfd.get_js_flow_definition_by_language(target_language)
        if not static_flow:
            static_flow = mfd.get_js_flow_definition_by_language(get_service_profile(sid.user).defaultLanguage)
    if static_flow:
        response.staticFlowHash = static_flow.hash_
        response.staticFlow = static_flow.definition
        response.staticFlowBrandings = static_flow.brandings

        if not get_friend_serviceidentity_connection(app_user, si.service_identity_user):
            # Fake a deleted connection between service and human user to be able to
            # start a flow with user, service and system data
            fake_friend_connection(app_user, si)
    else:
        response.staticFlowHash = None
        response.staticFlow = None
        response.staticFlowBrandings = []

    current_app_id = users.get_current_app_id()
    if current_app_id in si.appIds:
        response.error = None
    else:
        response.error = ErrorTO()

        other_app = get_app_by_id(si.app_id)
        m = users.get_current_mobile()
        if m.is_ios or m.is_android:
            response.error.caption = localize(target_language, "Install %(other_app_name)s",
                                              other_app_name=other_app.name)
            if m.is_ios:
                response.error.action = other_app.ios_appstore_ios_uri
            else:
                response.error.action = other_app.android_market_android_uri
        else:
            response.error.caption = response.error.action = None
        response.error.title = localize(target_language, "Error")
        response.error.message = localize(target_language,
                                          "This service is not supported by the %(current_app_name)s app. Please install the %(other_app_name)s app.",
                                          current_app_name=get_app_name_by_id(current_app_id),
                                          other_app_name=other_app.name)

    slog('T', app_user.email(), "com.mobicage.api.services.getActionInfo", service=response.email,
         tag=sid.tag, description=sid.description)
    slog(msg_="QR Code scan", function_=log_analysis.QRCODE_SCANNED, service=pp.user.email(), sid=sid.key().id(),
         service_identifier=si.identifier, supported_platform=True, from_rogerthat=True)
    return response


@expose(('api',))
@returns(StartServiceActionResponseTO)
@arguments(request=StartServiceActionRequestTO)
def startAction(request):
    from rogerthat.rpc import users
    current_user = users.get_current_user()
    mf_run_id = None if request.message_flow_run_id is MISSING else request.message_flow_run_id
    timestamp = None if request.timestamp is MISSING else request.timestamp
    poke_service(current_user, add_slash_default(users.User(request.email)), request.action, request.context, mf_run_id,
                 timestamp)
    return None


@expose(('api',))
@returns(PokeServiceResponseTO)
@arguments(request=PokeServiceRequestTO)
def pokeService(request):
    from rogerthat.rpc import users
    current_user = users.get_current_user()
    timestamp = None if request.timestamp is MISSING else request.timestamp
    poke_service_by_hashed_tag(current_user, add_slash_default(users.User(request.email)), request.hashed_tag,
                               request.context, timestamp)
    return None


@expose(('api',))
@returns(GetUserLinkResponseTO)
@arguments(request=GetUserLinkRequestTO)
def getUserLink(request):
    from rogerthat.rpc import users
    current_user = users.get_current_user()
    user_link = get_user_link(current_user, request.link)
    return GetUserLinkResponseTO(link=user_link)


@expose(('api',))
@returns(GetMenuIconResponseTO)
@arguments(request=GetMenuIconRequestTO)
def getMenuIcon(request):
    from rogerthat.dal.service import get_service_menu_item_by_coordinates
    from rogerthat.rpc import users
    service_identity_user = add_slash_default(users.User(request.service))
    get_service_identity(service_identity_user)  # azzerts
    smd = get_service_menu_item_by_coordinates(service_identity_user, request.coords)
    if not smd:
        return None
    response = GetMenuIconResponseTO()
    size = request.size
    icon, icon_hash = get_menu_icon(smd, service_identity_user, users.get_current_user())
    response.icon = unicode(base64.encodestring(render_menu_icon(icon, size)))
    response.iconHash = icon_hash
    return response


@expose(('api',))
@returns(GetStaticFlowResponseTO)
@arguments(request=GetStaticFlowRequestTO)
def getStaticFlow(request):
    from rogerthat.dal.service import get_service_menu_item_by_coordinates
    from rogerthat.rpc import users
    service_identity_user = add_slash_default(users.User(request.service))
    get_service_identity(service_identity_user)  # azzerts

    smd = get_service_menu_item_by_coordinates(service_identity_user, request.coords)
    if not smd:
        logging.info("No menu item found with coords %s" % request.coords)
        return None

    if not smd.staticFlowKey:
        logging.info("Menu item %s doesn't reference a static flow" % request.coords)
        return None

    mfd = MessageFlowDesign.get(smd.staticFlowKey)
    static_flow = mfd.get_js_flow_definition_by_hash(request.staticFlowHash)
    if not static_flow:
        logging.info("No static flow found on MFD '%s' with hash %s" % (mfd.name, request.staticFlowHash))
        return None

    response = GetStaticFlowResponseTO()
    response.staticFlow = static_flow.definition
    return response


@expose(('api',))
@returns(PressMenuIconResponseTO)
@arguments(request=PressMenuIconRequestTO)
def pressMenuItem(request):
    from rogerthat.bizz.service import press_menu_item
    from rogerthat.rpc import users
    service_identity_user = add_slash_default(users.User(request.service))
    get_service_identity(service_identity_user)  # azzerts
    mf_run_id = None if request.message_flow_run_id is MISSING else request.message_flow_run_id
    hashed_tag = None if request.hashed_tag is MISSING else request.hashed_tag
    timestamp = None if request.timestamp is MISSING else request.timestamp
    user = users.get_current_user()
    press_menu_item(user, service_identity_user, request.coords, request.context,
                    request.generation, mf_run_id, hashed_tag, timestamp)


@expose(('api',))
@returns(ShareServiceResponseTO)
@arguments(request=ShareServiceRequestTO)
def shareService(request):
    from rogerthat.bizz.friends import share_service_identity
    from rogerthat.rpc import users
    app_user = users.get_current_user()
    share_service_identity(app_user,
                           add_slash_default(users.User(request.service_email)),
                           create_app_user(users.User(request.recipient), get_app_id_from_app_user(app_user)))
    return ShareServiceResponseTO()


@expose(('api',))
@returns(FindServiceResponseTO)
@arguments(request=FindServiceRequestTO)
def findService(request):
    from rogerthat.bizz.service import find_service
    from rogerthat.rpc import users
    response_to = find_service(users.get_current_user(),
                               request.search_string,
                               request.geo_point,
                               MISSING.default(request.organization_type, ServiceProfile.ORGANIZATION_TYPE_UNSPECIFIED),
                               MISSING.default(request.cursor, None),
                               50 if request.avatar_size is MISSING else min(67, request.avatar_size),  # max 67px
                               MISSING.default(request.hashed_tag, None))
    return response_to


@expose(('api',))
@returns(SendApiCallResponseTO)
@arguments(request=SendApiCallRequestTO)
def sendApiCall(request):
    # type: (SendApiCallRequestTO) -> SendApiCallResponseTO
    if not request.service:
        logging.info('Received sendApiCall request without service. Ignoring.')
        return SendApiCallResponseTO()

    from rogerthat.bizz.service import send_api_call
    from rogerthat.rpc import users
    result = send_api_call(users.get_current_user(), add_slash_default(users.User(request.service)), request.id,
                           request.method, request.params, request.hashed_tag, request.synchronous)
    response = SendApiCallResponseTO()
    if request.synchronous:
        response.result = result
    return response


@expose(('api',))
@returns(UpdateUserDataResponseTO)
@arguments(request=UpdateUserDataRequestTO)
def updateUserData(request):
    from rogerthat.bizz.service import set_user_data, set_user_data_object
    from rogerthat.rpc import users

    if request.type not in (MISSING, None, UpdateUserDataRequestTO.DATA_TYPE_USER):
        logging.error("Ignoring updateUserData for unknown type '%s'", request.type)
        return UpdateUserDataResponseTO()

    app_user = users.get_current_user()
    service_identity_user = add_slash_default(users.User(request.service))
    keys = MISSING.default(request.keys, [])
    values = MISSING.default(request.values, [])

    if keys and values:  # deprecated way
        user_data = {key: json.loads(value)["v"] if value else None
                     for key, value in zip(keys, values)}
        set_user_data_object(service_identity_user, app_user, user_data, must_be_friends=False)
    else:
        replace = request.user_data not in (MISSING, None)
        data = request.user_data if replace else MISSING.default(request.data, None)
        set_user_data(service_identity_user, app_user, data, replace, must_be_friends=False)

    return UpdateUserDataResponseTO()
