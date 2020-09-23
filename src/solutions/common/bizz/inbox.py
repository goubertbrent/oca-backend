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
import logging
import os
import time
from StringIO import StringIO
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from types import NoneType

import jinja2
from babel.dates import format_datetime
from google.appengine.ext import deferred, db

import solutions
from mcfw.properties import long_property
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.rtemail import EMAIL_REGEX
from rogerthat.consts import SCHEDULED_QUEUE, DAY, MC_DASHBOARD
from rogerthat.dal import parent_key_unsafe
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.profile import get_service_profile
from rogerthat.models import App
from rogerthat.rpc import users
from rogerthat.service.api import system
from rogerthat.settings import get_server_settings
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import send_mail_via_mime, now, send_mail
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from rogerthat.utils.models import reconstruct_key
from rogerthat.utils.transactions import run_in_transaction
from shop.constants import LOGO_LANGUAGES
from shop.exceptions import InvalidEmailFormatException
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import SolutionModule, create_pdf
from solutions.common.bizz.broadcast_statistics import get_broadcast_statistics_excel
from solutions.common.bizz.loyalty import update_user_data_admins
from solutions.common.dal import get_solution_settings, get_solution_settings_or_identity_settings
from solutions.common.models import SolutionInboxMessage, SolutionSettings
from solutions.common.models.properties import SolutionUser
from solutions.common.utils import create_service_identity_user_wo_default
from solutions.jinja_extensions import TranslateExtension

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), '..', 'templates')]),
    extensions=[TranslateExtension, ])


@returns(NoneType)
@arguments(service_user=users.User, str_key=unicode, msg_params=dict)
def _send_styled_inbox_forwarders_email_reminder(service_user, str_key, msg_params=None):
    m = SolutionInboxMessage.get(str_key)
    if m.deleted == False and m.trashed == False and m.starred == False and m.reply_enabled == True and not m.child_messages:
        send_styled_inbox_forwarders_email(service_user, str_key, msg_params, True)


@returns(NoneType)
@arguments(service_user=users.User, str_key=unicode, msg_params=dict, reminder=bool)
def send_styled_inbox_forwarders_email(service_user, str_key, msg_params, reminder=False):
    m = SolutionInboxMessage.get(str_key)
    service_identity = m.service_identity
    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)

    def transl(key, **params):
        return common_translate(sln_settings.main_language, key, **params)

    chat_topic = transl(m.chat_topic_key)

    if m.category in (SolutionInboxMessage.CATEGORY_OCA_INFO, SolutionInboxMessage.CATEGORY_CITY_MESSAGE):
        subject = transl('there_is_a_new_message_in_your_inbox', name=m.sender.name)
    else:
        subject = transl('if-email-subject', function=chat_topic)
    if reminder:
        if not sln_i_settings.inbox_email_reminders_enabled:
            return
        subject = transl('inbox-forwarding-reminder-text', text=subject)

    settings = get_server_settings()
    service_profile = get_service_profile(service_user)
    community = get_community(service_profile.community_id)
    app = get_app_by_id(community.default_app)

    mimeRoot = MIMEMultipart('related')
    mimeRoot['Subject'] = subject
    mimeRoot['From'] = settings.senderEmail if app.type == App.APP_TYPE_ROGERTHAT else (
        "%s <%s>" % (community.name, app.dashboard_email_address))
    mimeRoot['To'] = ', '.join(sln_i_settings.inbox_mail_forwarders)

    mime = MIMEMultipart('alternative')
    mimeRoot.attach(mime)

    button_css = 'display: inline-block; margin-left: 0.5em; margin-right: 0.5em; -webkit-border-radius: 6px;' \
                 ' -moz-border-radius: 6px; border-radius: 6px; font-family: Arial; color: #ffffff; font-size: 14px;' \
                 ' background: #3abb9e; padding: 8px 16px 8px 16px; text-decoration: none;'
    if m.category in (SolutionInboxMessage.CATEGORY_OCA_INFO, SolutionInboxMessage.CATEGORY_CITY_MESSAGE):
        if_email_body_1 = u'%s %s' % (
            transl('there_is_a_new_message_in_your_inbox', name=m.sender.name),
            transl('login_to_dashboard_to_view_message', name=m.sender.name))
        if_email_body_2 = if_email_body_3_button = if_email_body_3_url = None
    else:
        if_email_body_1 = transl('if-email-body-1', if_name=msg_params['if_name'], function=chat_topic,
                                 app_name=community.name)
        if_email_body_2 = transl('if-email-body-2')
        dashboard_trans = transl('dashboard')
        service_email = sln_settings.login.email() if sln_settings.login else service_user.email()
        btn = u'<a href="https://dashboard.onzestadapp.be/customers/signin?email=%(service_email)s" style="%(button_css)s">%(dashboard)s</a>' % {
            'service_email': service_email,
            'button_css': button_css,
            'dashboard': dashboard_trans
        }
        if_email_body_3_button = transl('if-email-body-3-button', dashboard_button=btn)
        if_email_body_3_url = transl('if-email-body-3-url', dashboard_url='https://dashboard.onzestadapp.be/customers/signin?email=%s' % service_email)

    if_email_footer_1 = transl('if-email-footer-1', service_name=sln_settings.name, app_name=app.name)
    if_email_footer_2 = transl('if-email-footer-2')
    if_email_footer_3 = transl('if-email-footer-3')
    if_email_footer_4 = transl('if-email-footer-4')
    if_email_footer_5 = transl('if-email-footer-5')
    if_email_footer_6 = transl('if-email-footer-6')

    html_params = {
        'category': m.category,
        'if_email_body_1': if_email_body_1,
        'if_email_body_2': if_email_body_2,
        'if_email_body_3_button': if_email_body_3_button,
        'if_email_footer_1': if_email_footer_1,
        'if_email_footer_2': if_email_footer_2,
        'if_email_footer_3': if_email_footer_3,
        'if_email_footer_4': if_email_footer_4,
        'if_email_footer_5': if_email_footer_5,
        'if_email_footer_6': if_email_footer_6
    }

    text_params = {
        'category': m.category,
        'if_email_body_1': if_email_body_1,
        'if_email_body_2': if_email_body_2,
        'if_email_body_3_url': if_email_body_3_url,
        'if_email_footer_1': if_email_footer_1,
        'if_email_footer_2': if_email_footer_2,
        'if_email_footer_3': if_email_footer_3,
        'if_email_footer_4': if_email_footer_4,
        'if_email_footer_5': if_email_footer_5,
        'if_email_footer_6': if_email_footer_6
    }
    body_html = JINJA_ENVIRONMENT.get_template('emails/inbox_forwarded_message_html.tmpl').render(html_params)
    body = JINJA_ENVIRONMENT.get_template('emails/inbox_forwarded_message.tmpl').render(text_params)

    mime.attach(MIMEText(body.encode('utf-8'), 'plain', 'utf-8'))
    mime.attach(MIMEText(body_html.encode('utf-8'), 'html', 'utf-8'))

    with open(os.path.join(os.path.dirname(solutions.__file__), 'common', 'templates', 'emails', 'oca-email-header.png'), 'r') as f:
        img_data = f.read()

    img = MIMEImage(img_data, 'png')
    img.add_header('Content-Id', '<osa-footer>')
    img.add_header("Content-Disposition", "inline", filename="Onze Stad App footer")
    mimeRoot.attach(img)

    send_mail_via_mime(settings.senderEmail, sln_i_settings.inbox_mail_forwarders, mimeRoot)  # todo patch

    if not reminder:
        if str_key:
            deferred.defer(_send_styled_inbox_forwarders_email_reminder, service_user, str_key, msg_params,
                           _countdown=60 * 60 * 24, _queue=SCHEDULED_QUEUE)
        else:
            logging.debug("Ignoring reminder (no str_key given)")


@returns(SolutionInboxMessage)
@arguments(service_user=users.User, service_identity=unicode, category=unicode, category_key=unicode, sent_by_service=bool, user_details=[UserDetailsTO],
           timestamp=(int, long), message=unicode, reply_enabled=bool, picture_urls=[unicode], video_urls=[unicode], mark_as_read=bool)
def create_solution_inbox_message(service_user, service_identity, category, category_key, sent_by_service, user_details, timestamp, message, reply_enabled, picture_urls=None, video_urls=None, mark_as_read=False):
    sln_settings = get_solution_settings(service_user)
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    sim_parent = SolutionInboxMessage(parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
    sim_parent.category = category
    sim_parent.category_key = category_key
    sim_parent.last_timestamp = timestamp
    sim_parent.last_message = message
    sim_parent.parent_message_key = None
    sim_parent.reply_enabled = reply_enabled
    sim_parent.child_messages = []

    sim_parent.sent_by_service = sent_by_service
    sim_parent.sender = SolutionUser.fromTO(user_details[0]) if user_details else None
    sim_parent.message_key = None
    sim_parent.timestamp = timestamp
    sim_parent.message = message
    if picture_urls is None:
        picture_urls = []
    sim_parent.picture_urls = picture_urls
    if video_urls is None:
        video_urls = []
    sim_parent.video_urls = video_urls
    sim_parent.read = mark_as_read
    sim_parent.starred = False
    sim_parent.trashed = False
    sim_parent.deleted = False
    sim_parent.put()

    if not mark_as_read and SolutionModule.LOYALTY in sln_settings.modules:
        deferred.defer(update_user_data_admins, service_user, service_identity)
    return sim_parent


def send_inbox_info_messages_to_services(service_users, sender, message,
                                         category=SolutionInboxMessage.CATEGORY_OCA_INFO):
    # type: (list[users.User], users.User, unicode, unicode) -> None
    from solutions.common.bizz.service import new_inbox_message
    sender_settings = get_solution_settings(sender)
    service_profile = get_service_profile(sender)
    sender_user_details = UserDetailsTO(email=sender.email(),
                                        name=sender_settings.name,
                                        avatar_url=service_profile.avatarUrl,
                                        language=service_profile.defaultLanguage)
    sln_settings_cache = {model.service_user: model for model in db.get([SolutionSettings.create_key(user)
                                                                         for user in service_users])}
    tasks = [create_task(new_inbox_message, sln_settings_cache[user], message,
                         category=category, reply_enabled=False, send_to_forwarders=True,
                         user_details=sender_user_details) for user in service_users]
    schedule_tasks(tasks)


@returns(tuple)
@arguments(service_user=users.User, key=unicode, sent_by_service=bool, user_details=[UserDetailsTO],
           timestamp=(int, long), message=unicode, picture_urls=[unicode], video_urls=[unicode], mark_as_unread=bool, mark_as_read=bool, mark_as_trashed=bool)
def add_solution_inbox_message(service_user, key, sent_by_service, user_details, timestamp, message, picture_urls=None, video_urls=None, mark_as_unread=True, mark_as_read=False, mark_as_trashed=False):
    def trans(message, picture_urls, video_urls):
        sln_settings = get_solution_settings(service_user)
        sim_parent = SolutionInboxMessage.get(reconstruct_key(db.Key(key)))
        sim_reply = SolutionInboxMessage(parent=sim_parent)
        sim_reply.sent_by_service = sent_by_service
        sim_reply.sender = SolutionUser.fromTO(user_details[0]) if user_details else None
        sim_reply.message_key = None
        sim_reply.parent_message_key = sim_parent.message_key
        sim_reply.timestamp = timestamp
        sim_reply.message = message
        if picture_urls is None:
            picture_urls = []
        sim_reply.picture_urls = picture_urls
        if video_urls is None:
            video_urls = []
        sim_reply.video_urls = video_urls
        sim_reply.put()

        sim_parent.child_messages.append(sim_reply.id)
        sim_parent.last_timestamp = timestamp

        if not message:
            if picture_urls:
                message = common_translate(sln_settings.main_language, '<Picture>')
            elif video_urls:
                message = common_translate(sln_settings.main_language, '<Video>')

        sim_parent.last_message = message
        if mark_as_unread:
            sim_parent.read = False
        if mark_as_read:
            sim_parent.read = True
        if mark_as_trashed:
            sim_parent.trashed = True
        else:
            sim_parent.trashed = False
        sim_parent.deleted = False
        sim_parent.put()

        if SolutionModule.LOYALTY in sln_settings.modules:
            if mark_as_read or mark_as_unread or mark_as_trashed:
                deferred.defer(update_user_data_admins, service_user, sim_parent.service_identity, _transactional=True)
        return sim_parent, sim_reply

    return run_in_transaction(trans, True, message, picture_urls, video_urls)


class _MessagesExport(object):
    incomming_messages = long_property('1')
    child_messages = long_property('2')

    def __init__(self):
        self.incomming_messages = 0
        self.child_messages = 0

    @property
    def total_messages(self):
        return self.incomming_messages + self.child_messages


@returns(tuple)
@arguments(service_user=users.User, service_identity=unicode)
def export_inbox_messages(service_user, service_identity):
    tmpl_path = 'pdfs/inbox_export.html'
    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
    all_parent_messages = list(SolutionInboxMessage.get_all_by_service(
        service_user, service_identity, now() - DAY * 365))

    all_messages = list()
    to_get = list()
    for parent_msg in all_parent_messages:
        to_get.extend([SolutionInboxMessage.create_key(child, parent_msg.key()) for child in parent_msg.child_messages])

    inbox_messages_months_dict = dict()
    for i in range(1, 13):
        inbox_messages_months_dict[i] = _MessagesExport()

    parent_messages_children = dict()
    for child in SolutionInboxMessage.get(to_get):
        if child.parent_key() not in parent_messages_children:
            parent_messages_children[child.parent_key()] = list()
        parent_messages_children[child.parent_key()].append(child)
    for parent_msg in all_parent_messages:
        parent_msg.datetime = format_datetime(parent_msg.timestamp, format='EEEE d MMM y HH:mm',
                                              locale=sln_settings.main_language)
        parent_msg.message = parent_msg.message.replace('\n', '<br />').replace('\t', '&nbsp;&nbsp;')
        if parent_msg.trashed:
            parent_msg.inbox = SolutionInboxMessage.INBOX_NAME_TRASH
        elif parent_msg.starred:
            parent_msg.inbox = SolutionInboxMessage.INBOX_NAME_STARRED
        elif not parent_msg.read:
            parent_msg.inbox = SolutionInboxMessage.INBOX_NAME_UNREAD
        else:
            parent_msg.inbox = SolutionInboxMessage.INBOX_NAME_READ
        parent_msg.inbox = parent_msg.inbox.title()
        parent_msg.children = list()

        # xls file
        parent_msg_month = time.localtime(parent_msg.timestamp).tm_mon
        inbox_messages_months_dict[parent_msg_month].incomming_messages += 1

        if parent_msg.key() in parent_messages_children:
            for child in parent_messages_children[parent_msg.key()]:
                child.datetime = format_datetime(child.timestamp, format='EEEE d M y HH:mm',
                                                 locale=sln_settings.main_language)
                child.message = child.message.replace('\n', '<br />').replace('\t', '&nbsp;&nbsp;')
                if child.trashed:
                    child.inbox = SolutionInboxMessage.INBOX_NAME_TRASH
                elif child.starred:
                    child.inbox = SolutionInboxMessage.INBOX_NAME_STARRED
                elif not child.read:
                    child.inbox = SolutionInboxMessage.INBOX_NAME_UNREAD
                else:
                    child.inbox = SolutionInboxMessage.INBOX_NAME_READ
                child.inbox = child.inbox.title()
                parent_msg.children.append(child)
                child_msg_month = time.localtime(child.timestamp).tm_mon
                inbox_messages_months_dict[child_msg_month].child_messages += 1
        all_messages.append(parent_msg)

    if sln_settings.main_language in LOGO_LANGUAGES:
        logo_path = 'templates/img/osa_white_' + sln_settings.main_language + '_250.jpg'
    else:
        logo_path = 'templates/img/osa_white_en_250.jpg'
    tmpl_variables = {
        'sln_i_settings': sln_i_settings,
        'messages': all_messages,
        'logo_path': logo_path
    }
    source_html = JINJA_ENVIRONMENT.get_template(tmpl_path).render(tmpl_variables)
    html_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    pdf = create_pdf(source_html, html_dir, "")
    message_statistics = create_message_statistics_excel(inbox_messages_months_dict, sln_settings.main_language)
    return pdf, message_statistics


def create_message_statistics_excel(messages_months_dict, language):
    import xlwt
    # amount of messages per month
    # month | incoming messages | replies | total messages

    def transl(key):
        return common_translate(language, key)

    column_month = 0
    column_messages = 1
    column_replies = 2
    column_total_messages = 3
    bold_style = xlwt.XFStyle()
    bold_style.font.bold = True
    book = xlwt.Workbook(encoding="utf-8")

    # Excel has a 31 character limit for sheet names
    messages_sheet = book.add_sheet(transl('inbox_messages')[0:31])
    messages_sheet.write(0, column_month, transl('month').title(), bold_style)
    messages_sheet.write(0, column_messages, transl('incoming_messages'), bold_style)
    messages_sheet.write(0, column_replies, transl('replies'), bold_style)
    messages_sheet.write(0, column_total_messages, transl('total_messages'), bold_style)
    messages_sheet.col(column_month).width = 5000
    messages_sheet.col(column_messages).width = 5000
    messages_sheet.col(column_replies).width = 5000
    messages_sheet.col(column_total_messages).width = 5000

    # start with last month, end with current month
    current_month = datetime.datetime.now().month
    i = 0
    for i in xrange(1, len(messages_months_dict) + 1):
        month_string = format_datetime(time.mktime((2015, current_month, 1, 12, 0, 0, 0, 0, 0)), format='MMMM',
                                       locale=language)
        messages_sheet.write(i, column_month, month_string)
        messages_sheet.write(i, column_messages, messages_months_dict[current_month].incomming_messages)
        messages_sheet.write(i, column_replies, messages_months_dict[current_month].child_messages)
        messages_sheet.write(i, column_total_messages, messages_months_dict[current_month].total_messages)
        current_month -= 1
        if current_month < 1:
            current_month = 12

    excel_file = StringIO()
    book.save(excel_file)
    return excel_file.getvalue()


def send_statistics_export_email(service_user, service_identity, email, sln_settings):
    if not EMAIL_REGEX.match(email):
        raise InvalidEmailFormatException(email)
    deferred.defer(_deferred_statistics_email_export, service_user, service_identity, sln_settings.main_language, email)


def _deferred_statistics_email_export(service_user, service_identity, lang, email):
    users.set_user(service_user)
    try:
        messages_pdf, message_statistics_excel = export_inbox_messages(service_user, service_identity)
        broadcast_statistics = get_broadcast_statistics_excel(service_user, service_identity)
        flow_statistics_excel = base64.b64decode(system.export_flow_statistics(service_identity))
    finally:
        users.clear_user()
    cur_date = format_datetime(now(), format='d-M-yyyy', locale=lang)
    subject = common_translate(lang, 'inbox_messages_export_for_date', date=cur_date)
    body_text = common_translate(lang, 'see_attachment_for_detailed_statistics')
    attachment_name_pdf = 'Inbox ' + cur_date + '.pdf'
    attachment_name_inbox_excel = 'Inbox messages ' + cur_date + '.xls'
    attachment_name_broadcast_statistics = common_translate(lang, 'broadcast_statistics') + '.xls'
    attachment_name_flow_statistics_excel = 'Flow statistics ' + cur_date + '.xls'

    attachments = []
    attachments.append((attachment_name_pdf,
                        base64.b64encode(messages_pdf)))
    attachments.append((attachment_name_inbox_excel,
                        base64.b64encode(message_statistics_excel)))
    attachments.append((attachment_name_broadcast_statistics,
                        base64.b64encode(broadcast_statistics)))
    attachments.append((attachment_name_flow_statistics_excel,
                        base64.b64encode(flow_statistics_excel)))

    send_mail(MC_DASHBOARD.email(), email, subject, body_text, attachments=attachments)
