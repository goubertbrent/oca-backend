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
import hashlib
import json
import logging
import uuid
from xml.dom.minidom import parseString, parse

from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred, ndb

from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments, parse_complex_value, serialize_complex_value
from rogerthat.bizz.i18n import get_translator
from rogerthat.bizz.messaging import sendMessage, sendForm, ReservedTagException, InvalidFlowParamsException, \
    send_apple_push_message
from rogerthat.bizz.service import get_mfr_sik, get_mfr_api_key, InvalidValueException
from rogerthat.bizz.service.mfd import message_flow_design_to_xml, get_message_flow_design_context, \
    get_message_flow_by_key_or_name, compress_js_flow_definition
from rogerthat.bizz.service.mfd.mfd_javascript import generate_js_flow_cached
from rogerthat.bizz.service.mfd.sub import MessageFlowRunSub, MemberRunSub
from rogerthat.capi.messaging import startFlow
from rogerthat.consts import MC_RESERVED_TAG_PREFIX, MC_DASHBOARD
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.profile import get_profile_infos, get_service_profile
from rogerthat.dal.service import get_service_identity
from rogerthat.models import MessageFlowDesign, MessageFlowRunRecord, UserProfile, FriendServiceIdentityConnection, \
    ServiceTranslation, CustomMessageFlowDesign, UserServiceData
from rogerthat.rpc import users
from rogerthat.rpc.models import RpcCAPICall, Mobile
from rogerthat.rpc.rpc import logError, mapping, CAPI_KEYWORD_PUSH_DATA
from rogerthat.rpc.service import ServiceApiException
from rogerthat.settings import get_server_settings
from rogerthat.to.messaging import UserMemberTO, BaseMemberTO, StartFlowRequestTO, StartFlowResponseTO
from rogerthat.to.messaging.service_callback_results import FlowStartResultCallbackResultTO, \
    MessageCallbackResultTypeTO, FormCallbackResultTypeTO
from rogerthat.to.push import StartLocalFlowNotification
from rogerthat.utils import try_or_defer, now, bizz_check, get_full_language_string
from rogerthat.utils.app import get_app_user_tuple, get_app_id_from_app_user
from rogerthat.utils.crypto import md5_hex
from rogerthat.utils.service import get_service_user_from_service_identity_user, \
    get_identity_from_service_identity_user, remove_slash_default


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class MessageFlowNotFoundException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_MESSAGE_FLOW + 1,
                                     "Message flow definition not found!")


class NonFriendMembersException(ServiceApiException):

    def __init__(self, non_members):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_MESSAGE_FLOW + 2,
                                     "Non-friend members supplied!", non_members=non_members)


class MessageFlowNotValidException(ServiceApiException):

    def __init__(self, error):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_MESSAGE_FLOW + 3,
                                     "Message flow is not valid and cannot be executed in its current state!", error=error)


class MessageParentKeyCannotBeUsedWithMultipleParents(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_MESSAGE_FLOW + 4,
                                     "You can not use the message parent key with multiple members.")


class NoMembersException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_MESSAGE_FLOW + 5,
                                     "No members supplied!")


class MessageFlowDesignInUseException(ServiceApiException):

    def __init__(self, reason):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_MESSAGE_FLOW + 6,
                                     "Message flow can not be deleted", reason=reason)


class InvalidMessageFlowXmlException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_MESSAGE_FLOW + 7,
                                     "The XML is not conform to the message flow design XML schema")


class MessageFlowDesignValidationException(ServiceApiException):

    def __init__(self, message_flow_design):
        self.message_flow_design = message_flow_design
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_MESSAGE_FLOW + 8,
                                     "Message flow design is not valid: %s" % message_flow_design.validation_error,
                                     validation_error=message_flow_design.validation_error)


class InvalidMessageFlowLanguageException(ServiceApiException):

    def __init__(self, expected_language, current_language):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_MESSAGE_FLOW + 9,
                                     "Unexpected language specified in message flow design XML. Expected language '%s', got language '%s'." % (
                                         expected_language, current_language),
                                     expected_language=expected_language, current_language=current_language)


class InvalidMessageAttachmentException(ServiceApiException):

    def __init__(self, reason):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_MESSAGE_FLOW + 10, reason)


def _validate_start_flow(service_identity_user, parent_message_key, members, check_friends=True,
                         tag=None, allow_reserved_tag=False, flow_params=None):
    if not members:
        raise NoMembersException()

    if parent_message_key and len(members) > 1:
        raise MessageParentKeyCannotBeUsedWithMultipleParents()

    if tag and not allow_reserved_tag and tag.startswith(MC_RESERVED_TAG_PREFIX):
        raise ReservedTagException()

    # Create list with ServiceFriendKeys for the members
    if check_friends:
        fsic_keys = [FriendServiceIdentityConnection.createKey(member, service_identity_user) for member in members]
        fsics = db.get(fsic_keys)  # db.get returns a list of found and None
        non_friends = []
        for (member, fsic) in zip(members, fsics):
            if not fsic:
                m = BaseMemberTO()
                human_user, m.app_id = get_app_user_tuple(member)
                m.member = human_user.email()
                non_friends.append(m)

        if non_friends:
            raise NonFriendMembersException(serialize_complex_value(non_friends, BaseMemberTO, True))
    if flow_params:
        try:
            json.loads(flow_params)
        except ValueError:
            raise InvalidFlowParamsException()


def _create_message_flow_run(service_user, service_identity_user, message_flow_run_key=None, result_callback=True,
                             tag=None, flow_params=None):
    message_flow_run_id = message_flow_run_key or str(uuid.uuid4())
    mfr = MessageFlowRunRecord(key_name=MessageFlowRunRecord.createKeyName(service_user, message_flow_run_id))
    mfr.post_result_callback = result_callback
    mfr.tag = tag
    mfr.creationtime = now()
    mfr.service_identity = service_identity_user.email()
    mfr.flow_params = flow_params
    mfr.put()
    return mfr


# TODO: remove
@returns(unicode)
@arguments(service_identity_user=users.User, message_parent_key=unicode,
           flow=(str, unicode, MessageFlowDesign, CustomMessageFlowDesign),
           members=[users.User], check_friends=bool, result_callback=bool, tag=unicode, context=unicode, key=unicode,
           force_language=unicode, allow_reserved_tag=bool, flow_params=unicode)
def start_flow(service_identity_user, message_parent_key, flow, members, check_friends, result_callback, tag=None,
               context=None, key=None, force_language=None, allow_reserved_tag=False, flow_params=None):
    # key is in fact a force_message_flow_run_id
    svc_user = get_service_user_from_service_identity_user(service_identity_user)

    if isinstance(flow, (str, unicode)):
        mfd = get_message_flow_by_key_or_name(svc_user, flow)
        if not mfd or not mfd.user == svc_user:
            raise MessageFlowNotFoundException()

        if mfd.status != MessageFlowDesign.STATUS_VALID:
            raise MessageFlowNotValidException(mfd.validation_error)
    else:
        mfd = flow

    _validate_start_flow(service_identity_user, message_parent_key, members, check_friends, tag, allow_reserved_tag,
                         flow_params)
    mfr = _create_message_flow_run(svc_user, service_identity_user, key, result_callback, tag, flow_params)
    message_flow_run_id = mfr.messageFlowRunId

    d = hashlib.sha256(message_flow_run_id)
    d.update('key for first message in flow!')

    try_or_defer(_execute_flow, service_identity_user, mfd, mfr, members, message_parent_key, context, d.hexdigest(),
                 force_language=force_language, tag=tag, _transactional=db.is_in_transaction())

    return message_flow_run_id


@returns(unicode)
@arguments(service_identity_user=users.User, thread_key=unicode, xml=unicode, members=[users.User],
           tag=unicode, context=unicode, force_language=unicode, download_attachments_upfront=bool,
           push_message=unicode, parent_message_key=unicode, flow=unicode, flow_params=unicode, check_friends=bool)
def start_local_flow(service_identity_user, thread_key, xml, members, tag=None, context=None,
                     force_language=None, download_attachments_upfront=False, push_message=None,
                     parent_message_key=None, flow=None, flow_params=None, check_friends=True):
    _validate_start_flow(service_identity_user, thread_key, members, tag=tag, check_friends=check_friends)
    service_user = get_service_user_from_service_identity_user(service_identity_user)
    if flow:
        if xml:
            raise InvalidValueException('xml', 'parameter "xml" cannot be set when property "flow" is set')
        mfd = get_message_flow_by_key_or_name(service_user, flow)
        if not mfd or not mfd.user == service_user:
            raise MessageFlowNotFoundException()

        if mfd.status != MessageFlowDesign.STATUS_VALID:
            raise MessageFlowNotValidException(mfd.validation_error)
        xml = mfd.xml

    js_flow_dict = generate_js_flow_cached(service_user, xml, context, minify=False,
                                           parent_message_key=parent_message_key, must_validate=True)
    # js_flow_dict = { language : (<compiled JS flow>, brandings, attachments) }
    if force_language and force_language is not MISSING:
        if force_language not in js_flow_dict:
            raise InvalidMessageFlowLanguageException(json.dumps(js_flow_dict.keys()), force_language)
        forced_flow = js_flow_dict[force_language]
    else:
        forced_flow = None

    extra_user = [] if service_user == MC_DASHBOARD else [service_identity_user]
    profile_infos = {profile_info.user: profile_info for profile_info in get_profile_infos(members + extra_user)}

    mfr = _create_message_flow_run(service_user, service_identity_user, result_callback=False, tag=tag)
    message_flow_run_id = mfr.messageFlowRunId

    for app_user in members:
        if forced_flow:
            flow_definition, brandings, attachments = forced_flow
        else:
            target_language = profile_infos[app_user].language
            if target_language not in js_flow_dict:
                # fall back to service default language
                sp = get_service_profile(service_user)
                target_language = sp.defaultLanguage if sp else js_flow_dict.keys()[0]
                if target_language not in js_flow_dict:
                    if len(js_flow_dict) == 1:
                        target_language = js_flow_dict.keys()[0]
                    else:
                        raise InvalidMessageFlowLanguageException(json.dumps(js_flow_dict.keys()), target_language)

            flow_definition, brandings, attachments = js_flow_dict[target_language]

        force_skip_attachments_download = False
        mobiles = profile_infos[app_user].mobiles
        if push_message:
            for mobile_detail in mobiles:
                if mobile_detail.type_ == Mobile.TYPE_IPHONE_HTTP_APNS_KICK and mobile_detail.pushId:
                    force_skip_attachments_download = True
                    break

        request = StartFlowRequestTO()
        request.attachments_to_dwnl = attachments if download_attachments_upfront and not force_skip_attachments_download else list()
        request.brandings_to_dwnl = brandings
        request.service = remove_slash_default(service_identity_user).email()
        request.static_flow = compress_js_flow_definition(flow_definition)
        request.static_flow_hash = unicode(md5_hex(flow_definition))
        request.parent_message_key = thread_key
        request.message_flow_run_id = message_flow_run_id
        request.flow_params = flow_params
        if service_user == MC_DASHBOARD:
            sender_name = get_app_by_id(get_app_id_from_app_user(app_user)).name
        else:
            sender_name = profile_infos[service_identity_user].name
        kwargs = {
            CAPI_KEYWORD_PUSH_DATA: StartLocalFlowNotification(sender_name, push_message)
        }
        startFlow(start_flow_response_handler, logError, app_user, request=request, **kwargs)

        if push_message:
            send_apple_push_message(push_message, sender_name, mobiles)

    return message_flow_run_id


@mapping('com.mobicage.capi.message.start_flow_response_handler')
@returns()
@arguments(context=RpcCAPICall, result=StartFlowResponseTO)
def start_flow_response_handler(context, result):
    pass


def _create_message_flow_run_xml_doc(service_identity_user, message_flow_design, message_flow_run_record, members,
                                     force_language):
    service_user = get_service_user_from_service_identity_user(service_identity_user)

    if not message_flow_design.xml:
        # Must regenerate xml
        subflowdict = get_message_flow_design_context(message_flow_design)
        translator = get_translator(service_user, ServiceTranslation.MFLOW_TYPES)
        definition_doc = parseString(message_flow_design_to_xml(
            service_user, message_flow_design, translator, subflowdict)[0].encode('utf-8'))
        message_flow_design.xml = definition_doc.toxml('utf-8')
        message_flow_design.put()
        logging.warning("Message flow design with empty xml property discovered!!!\nkey = %s" %
                        message_flow_design.key())
    else:
        definition_doc = parseString(message_flow_design.xml.encode('utf-8'))

    run = MessageFlowRunSub(launchTimestamp=message_flow_run_record.creationtime)
    si = get_service_identity(service_identity_user)
    run.set_serviceName(si.name)
    run.set_serviceDisplayEmail(si.qualifiedIdentifier or si.user.email())
    run.set_serviceEmail(si.user.email())
    run.set_flowParams(message_flow_run_record.flow_params)
    if si.serviceData:
        run.set_serviceData(json.dumps(si.serviceData.to_json_dict()))
    else:
        run.set_serviceData(si.appData)
    fallback_language = force_language or get_service_profile(service_user).defaultLanguage

    mf_languages = list()
    if definition_doc.documentElement.localName == 'messageFlowDefinitionSet':
        for definition_element in definition_doc.documentElement.childNodes:
            if definition_element.localName == 'definition':
                mf_languages.append(definition_element.getAttribute('language'))
    elif definition_doc.documentElement.localName == 'definition':
        mf_languages.append(fallback_language)
    else:
        azzert(False, "Unexpected tag name: %s" % definition_doc.documentElement.localName)

    # if force_language supplied, check if it's in mf_languages
    if force_language:
        bizz_check(force_language in mf_languages, "Can not run in %s." % get_full_language_string(force_language))

    userprofiles = get_profile_infos(members, expected_types=[UserProfile] * len(members))
    user_datas = ndb.get_multi([UserServiceData.createKey(member, service_identity_user) for member in members])
    for i, p in enumerate(userprofiles):
        member_run_language = force_language or (p.language if p.language in mf_languages else fallback_language)
        human_user, app_id = get_app_user_tuple(p.user)

        if user_datas[i]:
            user_data = json.dumps(user_datas[i].data)
        else:
            user_data = None
        run.add_memberRun(MemberRunSub(status="SUBMITTED", email=human_user.email(), name=p.name,
                                       language=member_run_language, appId=app_id, avatarUrl=p.avatarUrl, userData=user_data))

    xml = StringIO()
    xml.write("""<?xml version="1.0" encoding="utf-8"?>\n""")
    run.export(xml, 0, namespaceprefix_='', namespacedef_='xmlns="https://rogerth.at/api/1/MessageFlow.xsd"',
               name_='messageFlowRun')
    xml.reset()
    xml_doc = parse(xml)
    for member_run_child_node in xml_doc.documentElement.childNodes:
        if member_run_child_node.localName == "memberRun":
            break
    else:
        azzert(False, "No child nodes of type 'memberRun' found for xml:\n%s" % xml)

    # put memberRun in xml
    if definition_doc.documentElement.localName == 'messageFlowDefinitionSet':
        for definition_element in definition_doc.documentElement.childNodes:
            if definition_element.localName == 'definition':
                xml_doc.documentElement.insertBefore(definition_element, member_run_child_node)
    elif definition_doc.documentElement.localName == 'definition':
        xml_doc.documentElement.insertBefore(definition_doc.documentElement, member_run_child_node)
    else:
        azzert(False, "Unexpected tag name: %s" % definition_doc.documentElement.localName)

    return xml_doc


def _execute_flow(service_identity_user, message_flow_design, message_flow_run_record, members, message_parent_key,
                  context=None, resultKey=None, force_language=None, tag=None):
    logging.info("Executing message flow for %s with force_language %s" %
                 (service_identity_user.email(), force_language))

    xml_doc = _create_message_flow_run_xml_doc(service_identity_user, message_flow_design, message_flow_run_record,
                                               members, force_language)
    logging.info(xml_doc.toxml())
    xml = xml_doc.toxml("utf-8")

    settings = get_server_settings()

    headers = {
        'X-Nuntiuz-Service-Identifier-Key': get_mfr_sik(service_identity_user).sik,
        'X-Nuntiuz-Service-Identity': base64.b64encode(get_identity_from_service_identity_user(service_identity_user)),
        'X-Nuntiuz-Service-API-Key': get_mfr_api_key(service_identity_user).key().name(),
        'X-Nuntiuz-Shared-Secret': settings.secret,
        'X-Nuntiuz-MessageFlowRunId': message_flow_run_record.messageFlowRunId,
        'X-Nuntiuz-MessageParentKey': message_parent_key if message_parent_key else "",
        'X-Nuntiuz-Context': context if context else "",
        'X-Nuntiuz-ResultKey': resultKey,
        'Content-type': 'text/xml'
    }

    if tag:
        headers['X-Nuntiuz-Tag'] = tag.encode('utf')

    logging.debug('Executing flow with run id %s for members %s', message_flow_run_record.messageFlowRunId, members)
    result = urlfetch.fetch(
        "%s/api" % settings.messageFlowRunnerAddress, xml, "POST", headers, False, False, deadline=10 * 60)
    if result.status_code != 200:
        error_message = "MFR returned status code %d" % result.status_code
        if result.status_code == 400:
            logging.error(error_message, _suppress=False)
            raise deferred.PermanentTaskFailure(error_message)
        raise Exception(error_message)

    logging.debug('MFR response: %s', result.content)
    if len(members) == 1 and result.content:
        try:
            flow_start_result = parse_complex_value(FlowStartResultCallbackResultTO, json.loads(result.content), False)
            if isinstance(flow_start_result.value, MessageCallbackResultTypeTO):
                sendMessage(service_identity_user, [UserMemberTO(members[0], flow_start_result.value.alert_flags)],
                            flow_start_result.value.flags, 0, message_parent_key, flow_start_result.value.message,
                            flow_start_result.value.answers, None, flow_start_result.value.branding,
                            flow_start_result.value.tag, flow_start_result.value.dismiss_button_ui_flags, context,
                            key=resultKey, is_mfr=True, attachments=flow_start_result.value.attachments,
                            step_id=None if flow_start_result.value.step_id is MISSING else flow_start_result.value.step_id)
            elif isinstance(flow_start_result.value, FormCallbackResultTypeTO):
                sendForm(service_identity_user, message_parent_key, members[0], flow_start_result.value.message,
                         flow_start_result.value.form, flow_start_result.value.flags, flow_start_result.value.branding,
                         flow_start_result.value.tag, flow_start_result.value.alert_flags, context, key=resultKey,
                         is_mfr=True, attachments=flow_start_result.value.attachments,
                         step_id=None if flow_start_result.value.step_id is MISSING else flow_start_result.value.step_id)
        except:
            logging.exception("Failed to parse result from message flow runner.")
