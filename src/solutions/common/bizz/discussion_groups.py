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

import json
import logging
from datetime import datetime
from types import NoneType

from babel.dates import format_datetime, get_timezone
from google.appengine.ext import db, ndb
from typing import Optional, List

from mcfw.consts import MISSING
from mcfw.exceptions import HttpNotFoundException
from mcfw.rpc import returns, arguments
from rogerthat.models import Message
from rogerthat.models.properties.forms import FormResult
from rogerthat.models.utils import ndb_allocate_id
from rogerthat.rpc import users
from rogerthat.service.api import messaging
from rogerthat.to.messaging import MemberTO
from rogerthat.to.messaging.forms import MultiSelectFormTO, MultiSelectTO, ChoiceTO, FormTO
from rogerthat.to.messaging.service_callback_results import PokeCallbackResultTO, FormCallbackResultTypeTO, TYPE_FORM, \
    FormAcknowledgedCallbackResultTO, MessageCallbackResultTypeTO, TYPE_MESSAGE
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import now
from solutions import translate
from solutions.common.dal import get_solution_settings
from solutions.common.handlers import JINJA_ENVIRONMENT
from solutions.common.models import SolutionSettings, SolutionMainBranding
from solutions.common.models.discussion_groups import DiscussionGroup

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


@returns(DiscussionGroup)
@arguments(service_user=users.User, discussion_group_id=(int, long))
def get_discussion_group(service_user, discussion_group_id):
    # type: (users.User, int) -> Optional[DiscussionGroup]
    return DiscussionGroup.create_key(service_user, discussion_group_id).get()


@returns(str)
@arguments(service_user=users.User, discussion_group_id=(int, long))
def get_discussion_group_pdf(service_user, discussion_group_id):
    from xhtml2pdf import pisa
    discussion_group = get_discussion_group(service_user, discussion_group_id)
    if not discussion_group:
        raise HttpNotFoundException()

    sln_settings = get_solution_settings(service_user)
    fetch_messages = True
    messages = []
    cursor = None
    while fetch_messages:
        result = messaging.list_chat_messages(discussion_group.message_key, cursor)
        cursor = result.cursor
        messages += result.messages
        if not (cursor and len(result.messages) > 0):
            fetch_messages = False

    avatars = {}
    dates = {}
    for message in messages:
        if message.sender is None:
            # Message is sent by the service user
            message.sender = UserDetailsTO.create(email=service_user.email(),
                                                  name=sln_settings.name,
                                                  language=sln_settings.main_language,
                                                  avatar_url=None,
                                                  app_id='')
        dates[message.message_key] = format_datetime(datetime.utcfromtimestamp(message.timestamp),
                                                     locale=sln_settings.main_language,
                                                     tzinfo=get_timezone(sln_settings.timezone))
    variables = {
        'messages': messages,
        'avatars': avatars,
        'dates': dates,
        'discussion_group': discussion_group
    }
    path = 'pdfs/discussion_group_pdf.html'
    source_html = JINJA_ENVIRONMENT.get_template(path).render(variables)
    output_stream = StringIO()
    pisa.CreatePDF(src=source_html, dest=output_stream)
    return output_stream.getvalue()


@returns([DiscussionGroup])
@arguments(service_user=users.User)
def get_discussion_groups(service_user):
    return DiscussionGroup.list_ordered(service_user).fetch(None)


@returns(DiscussionGroup)
@arguments(service_user=users.User, topic=unicode, description=unicode, discussion_group_id=(int, long, NoneType))
def put_discussion_group(service_user, topic, description, discussion_group_id=None):
    is_new = discussion_group_id is None
    if is_new:
        discussion_group_id = ndb_allocate_id(DiscussionGroup)

        # Create the chat in Rogerthat
        from solutions.common.bizz.messaging import POKE_TAG_DISCUSSION_GROUPS
        tag = json.dumps({'id': discussion_group_id,
                          '__rt__.tag': POKE_TAG_DISCUSSION_GROUPS})
        members = []
        flags = messaging.ChatFlags.ALLOW_ANSWER_BUTTONS | messaging.ChatFlags.ALLOW_PICTURE
        message_key = messaging.start_chat(members, topic, description, tag=tag, flags=flags, default_sticky=True)

    @ndb.transactional()
    def trans():
        key = DiscussionGroup.create_key(service_user, discussion_group_id)
        if is_new:
            # Create the model
            discussion_group = DiscussionGroup(key=key, message_key=message_key, creation_timestamp=now())
        else:
            discussion_group = key.get()
            if not discussion_group:
                raise HttpNotFoundException()

        discussion_group.topic = topic
        discussion_group.description = description
        discussion_group.put()
        return discussion_group

    return trans()


@returns()
@arguments(service_user=users.User, discussion_group_id=(int, long))
def delete_discussion_group(service_user, discussion_group_id):
    key = DiscussionGroup.create_key(service_user, discussion_group_id)
    discussion_group = key.get()  # type: DiscussionGroup
    if not discussion_group:
        raise HttpNotFoundException()

    if discussion_group.message_key:
        sln_settings = get_solution_settings(service_user)
        message = translate(sln_settings.main_language, 'discussion_group_stopped')
        messaging.send_chat_message(discussion_group.message_key, message)
        messaging.update_chat(discussion_group.message_key, flags=messaging.ChatFlags.READ_ONLY)
    key.delete()


@returns(PokeCallbackResultTO)
@arguments(service_user=users.User, email=unicode, tag=unicode, result_key=unicode, context=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def poke_discussion_groups(service_user, email, tag, result_key, context, service_identity, user_details):
    # type: (users.User, unicode, unicode, unicode, unicode, unicode, List[UserDetailsTO]) -> PokeCallbackResultTO
    from solutions.common.bizz.messaging import POKE_TAG_DISCUSSION_GROUPS

    result = PokeCallbackResultTO()

    widget = MultiSelectTO()
    widget.choices = []
    widget.values = []
    app_user_email = user_details[0].toAppUser().email()
    for discussion_group in DiscussionGroup.list(service_user):
        widget.choices.append(ChoiceTO(label=discussion_group.topic, value=unicode(discussion_group.id)))
        if app_user_email in discussion_group.members:
            widget.values.append(unicode(discussion_group.id))

    sln_settings, sln_main_branding = db.get([SolutionSettings.create_key(service_user),
                                              SolutionMainBranding.create_key(service_user)])

    if widget.choices:
        form = MultiSelectFormTO()
        form.javascript_validation = None
        form.negative_button = translate(sln_settings.main_language, u'Cancel')
        form.negative_button_ui_flags = 0
        form.negative_confirmation = None
        form.positive_button = translate(sln_settings.main_language, u'Save')
        form.positive_button_ui_flags = Message.UI_FLAG_EXPECT_NEXT_WAIT_5
        form.positive_confirmation = None
        form.type = MultiSelectTO.TYPE
        form.widget = widget

        result.type = TYPE_FORM
        result.value = FormCallbackResultTypeTO()
        result.value.form = form
        result.value.message = translate(sln_settings.main_language, u'discussion_group_choices')
        result.value.tag = POKE_TAG_DISCUSSION_GROUPS
    else:
        result.type = TYPE_MESSAGE
        result.value = MessageCallbackResultTypeTO()
        result.value.answers = []
        result.value.dismiss_button_ui_flags = 0
        result.value.message = translate(sln_settings.main_language, u'no_discussion_groups_yet')
        result.value.tag = None

    result.value.alert_flags = Message.ALERT_FLAG_SILENT
    result.value.attachments = []
    result.value.branding = sln_main_branding.branding_key
    result.value.flags = Message.FLAG_AUTO_LOCK | Message.FLAG_ALLOW_DISMISS
    result.value.step_id = None

    return result


@returns(FormAcknowledgedCallbackResultTO)
@arguments(service_user=users.User, status=int, form_result=FormResult, answer_id=unicode, member=unicode,
           message_key=unicode, tag=unicode, received_timestamp=int, acked_timestamp=int, parent_message_key=unicode,
           result_key=unicode, service_identity=unicode, user_details=[UserDetailsTO])
def follow_discussion_groups(service_user, status, form_result, answer_id, member, message_key, tag, received_timestamp,
                             acked_timestamp, parent_message_key, result_key, service_identity, user_details):
    if answer_id != FormTO.POSITIVE or form_result in (None, MISSING) or form_result.result in (None, MISSING):
        return None

    app_user = user_details[0].toAppUser()
    app_user_email = app_user.email()
    selected_ids = map(long, form_result.result.values)

    to_add = []
    to_remove = []

    @ndb.transactional(xg=True)
    def trans():
        followed_new_group = False
        to_put = []
        for discussion_group in DiscussionGroup.list(service_user):  # type: DiscussionGroup
            was_following = app_user_email in discussion_group.members
            now_following = discussion_group.id in selected_ids

            if was_following != now_following:
                if now_following:
                    followed_new_group = True
                    logging.debug('Adding %s to discussion group "%s"', app_user_email, discussion_group.topic)
                    discussion_group.members.append(app_user_email)
                    to_add.append(discussion_group.message_key)
                else:
                    logging.debug('Removing %s from discussion group "%s"', app_user_email, discussion_group.topic)
                    discussion_group.members.remove(app_user_email)
                    to_remove.append(discussion_group.message_key)
                to_put.append(discussion_group)
        if to_put:
            ndb.put_multi(to_put)
        return followed_new_group

    followed_new_group = trans()
    for group_key in to_add:
        messaging.add_chat_members(group_key, [MemberTO.from_user(app_user)])
    for group_key in to_remove:
        messaging.delete_chat_members(group_key, [MemberTO.from_user(app_user)])

    sln_settings, sln_main_branding = db.get([SolutionSettings.create_key(service_user),
                                              SolutionMainBranding.create_key(service_user)])

    result = FormAcknowledgedCallbackResultTO()
    result.type = TYPE_MESSAGE
    result.value = MessageCallbackResultTypeTO()
    result.value.alert_flags = Message.ALERT_FLAG_VIBRATE
    result.value.answers = []
    result.value.attachments = []
    result.value.branding = sln_main_branding.branding_key
    result.value.dismiss_button_ui_flags = 0
    result.value.flags = Message.FLAG_AUTO_LOCK | Message.FLAG_ALLOW_DISMISS
    result.value.message = translate(sln_settings.main_language, u'Your changes have been saved.')
    if followed_new_group:
        result.value.message += u'\n\n%s' % translate(sln_settings.main_language,
                                                      u'you_can_find_discussion_groups_on_homescreen')
    result.value.step_id = None
    result.value.tag = None
    return result


@ndb.transactional()
@returns()
@arguments(service_user=users.User, parent_message_key=unicode, member=UserDetailsTO, timestamp=int,
           service_identity=unicode, tag=unicode)
def discussion_group_deleted(service_user, parent_message_key, member, timestamp, service_identity, tag):
    app_user_email = member.toAppUser().email()
    discussion_group_id = json.loads(tag)['id']
    discussion_group = get_discussion_group(service_user, discussion_group_id)
    if not discussion_group:
        logging.info('Discussion group %s not found', discussion_group_id)
        return

    if app_user_email not in discussion_group.members:
        logging.info('%s not found in discussion group %s', discussion_group_id)
        return

    discussion_group.members.remove(app_user_email)
    discussion_group.put()
