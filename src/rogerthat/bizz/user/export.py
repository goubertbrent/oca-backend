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

import datetime
import json
import logging
import os
from zipfile import ZipFile

import cloudstorage
from babel.dates import format_datetime
from google.appengine.api import urlfetch
from google.appengine.ext import deferred, db
from pipeline import pipeline

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.gcs import get_serving_url, upload_to_gcs
from rogerthat.bizz.job.workload import WorkloadPipeline
from rogerthat.consts import EXPORTS_BUCKET, DATA_EXPORT_QUEUE, DAY, DEBUG
from rogerthat.dal.friend import get_friends_map
from rogerthat.dal.messaging import get_message
from rogerthat.dal.profile import get_user_profile, get_profile_info, \
    get_profile_key
from rogerthat.dal.service import get_service_identity
from rogerthat.models import UserServiceData, Message, ChatMembers, UserDataExport, App
from rogerthat.models.properties.friend import BaseFriendDetail
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.templates import render
from rogerthat.to.messaging import AttachmentTO
from rogerthat.translations import localize
from rogerthat.utils import now, send_mail, is_flag_set
from rogerthat.utils.app import get_app_user_tuple, create_app_user_by_email
from rogerthat.utils.service import add_slash_default
from rogerthat.utils.transactions import run_in_transaction


@returns(unicode)
@arguments(app_user=users.User, data_export_email=unicode)
def export_user_data(app_user, data_export_email):
    human_user, app_id = get_app_user_tuple(app_user)
    date = format_datetime(datetime.datetime.now(), locale='en', format='yyyy_MM_dd')
    result_path = '/%s/users/%s/%s' % (EXPORTS_BUCKET, app_user.email(), date)

    def update():
        user_data_export_key = UserDataExport.create_key(app_user, date)
        user_data_export = UserDataExport.get(user_data_export_key)
        if user_data_export:
            return user_data_export.data_export_email

        user_data_export = UserDataExport(key=user_data_export_key)
        user_data_export.creation_time = now()
        user_data_export.data_export_email = data_export_email
        user_data_export.put()

        counter = ExportUserPipeline(result_path, human_user.email(), app_id, data_export_email)
        task = counter.start(return_task=True)
        task.add(queue_name=DATA_EXPORT_QUEUE, transactional=True)

        redirect_url = "%s/status?root=%s" % (counter.base_path, counter.pipeline_id)
        logging.info("export pipeline url: %s", redirect_url)
        return None

    return run_in_transaction(update, xg=True)


def _create_zip(result_path, human_user_email, app_id, data_export_email):
    zip_path = os.path.join(result_path, 'result.zip')
    with cloudstorage.open(zip_path, 'w') as zip_stream:
        with ZipFile(zip_stream, 'w', allowZip64=True) as bzf:
            for f in cloudstorage.listbucket(os.path.join(result_path, 'result')):
                with cloudstorage.open(f.filename, 'r') as file_stream:
                    filename = f.filename.replace('%s/result/' % result_path, '')
                    for chunk in file_stream:
                        bzf.writestr(filename, chunk)
    download_url = get_serving_url(zip_path)
    deferred.defer(_send_export_email, result_path, human_user_email, app_id, data_export_email, download_url,
                   _queue=DATA_EXPORT_QUEUE)


def _send_export_email(result_path, human_user_email, app_id, data_export_email, download_url):
    logging.info(download_url)
    app_user = create_app_user_by_email(human_user_email, app_id)
    user_profile, app = db.get([get_profile_key(app_user), App.create_key(app_id)])

    subject = localize(user_profile.language, "user_data_download_ready_summary")
    variables = dict(name=user_profile.name,
                     link=download_url,
                     app=app)
    body = render("data_download_ready_email", [user_profile.language], variables)
    html = render("data_download_ready_email_html", [user_profile.language], variables)
    server_settings = get_server_settings()

    email_receivers = [data_export_email]
    if app.is_default:
        email_sender = server_settings.senderEmail
    else:
        email_sender = ("%s <%s>" % (app.name, app.dashboard_email_address))

    send_mail(email_sender, email_receivers, subject, body, html=html)
    deferred.defer(_cleanup_export, result_path, _countdown=4 * DAY, _queue=DATA_EXPORT_QUEUE)


def _cleanup_export(result_path):
    for f in cloudstorage.listbucket(result_path):
        cloudstorage.delete(f.filename)


class ExportUserEmailPipeline(WorkloadPipeline):

    def run(self, result_path, human_user_email, app_id, data_export_email):
        deferred.defer(_create_zip, result_path, human_user_email, app_id, data_export_email, _queue=DATA_EXPORT_QUEUE)


class ExportUserPipeline(WorkloadPipeline):

    def run(self, result_path, human_user_email, app_id, data_export_email):
        p_friends = yield ExportUserFriendsPipeline(result_path, human_user_email, app_id)
        p_messages = yield ExportUserMessagesPipeline(result_path, human_user_email, app_id)
        p_profile = yield ExportUserProfilePipeline(result_path, human_user_email, app_id)
        with pipeline.After(p_friends, p_messages, p_profile):
            yield ExportUserEmailPipeline(result_path, human_user_email, app_id, data_export_email)

    def finalized(self):
        if self.was_aborted:
            logging.error('%s was aborted', self, _suppress=False)
            return
        logging.info('%s was finished', self)


class ExportUserServicePipeline(WorkloadPipeline):

    def run(self, result_path, human_user_email, app_id, service_identity_email):
        app_user = create_app_user_by_email(human_user_email, app_id)
        service_identity_user = add_slash_default(users.User(service_identity_email))
        si = get_service_identity(service_identity_user)
        ud = UserServiceData.createKey(app_user, add_slash_default(service_identity_user)).get()
        if ud:
            user_data = ud.data
        else:
            user_data = None

        s = {
            'name': si.name if si else None,
            'data': {
                'user': user_data
            }
        }

        with cloudstorage.open(os.path.join(result_path, 'result', 'services', service_identity_user.email(), 'service.json'), 'w') as gcs_file:
            gcs_file.write(json.dumps({
                'service': s
            }))


class ExportUserFriendsPipeline(WorkloadPipeline):

    def run(self, result_path, human_user_email, app_id):
        app_user = create_app_user_by_email(human_user_email, app_id)
        friend_map = get_friends_map(app_user)

        friends = []
        for fd in friend_map.friendDetails:
            f = {}
            if fd.type == BaseFriendDetail.TYPE_USER:
                f['type'] = 'user'
            elif fd.type == BaseFriendDetail.TYPE_SERVICE:
                f['type'] = 'service'
                yield ExportUserServicePipeline(result_path, human_user_email, app_id, fd.email)
            else:
                logging.warn('Friend type not implemented')
                continue

            f['name'] = fd.name
            if fd.existence == BaseFriendDetail.FRIEND_EXISTENCE_ACTIVE:
                f['existence'] = 'active'
            elif fd.existence == BaseFriendDetail.FRIEND_EXISTENCE_DELETE_PENDING:
                f['existence'] = 'delete_pending'
            elif fd.existence == BaseFriendDetail.FRIEND_EXISTENCE_DELETED:
                f['existence'] = 'deleted'
            elif fd.existence == BaseFriendDetail.FRIEND_EXISTENCE_NOT_FOUND:
                f['existence'] = 'not_found'
            elif fd.existence == BaseFriendDetail.FRIEND_EXISTENCE_INVITE_PENDING:
                f['existence'] = 'invite_pending'

            friends.append(f)

        with cloudstorage.open(os.path.join(result_path, 'result', 'friends', 'friends.json'), 'w') as gcs_file:
            gcs_file.write(json.dumps({
                'friends': friends
            }))


class ExportUserDownloadAttachmentPipeline(WorkloadPipeline):

    def run(self, result_path, target_path, content_type, download_url):
        try:
            result = urlfetch.fetch(download_url, deadline=5 if DEBUG else 55)
            if result.status_code == 200:
                upload_to_gcs(result.content, content_type, os.path.join(result_path, 'result', target_path))
        except urlfetch.Error:
            logging.warn('ExportUserDownloadAttachmentPipeline failed with url: %s', download_url, exc_info=1)


class ExportUserMessagePipeline(WorkloadPipeline):

    def run(self, result_path, human_user_email, app_id, pmk):
        app_user = create_app_user_by_email(human_user_email, app_id)
        parent_message = get_message(pmk, None)
        is_chat = is_flag_set(Message.FLAG_DYNAMIC_CHAT, parent_message.flags)
        if is_chat:
            chat_members_containing_user = list(ChatMembers.list_by_thread_and_chat_member(pmk, app_user.email()))
            azzert(chat_members_containing_user)
        else:
            azzert(app_user in parent_message.members)
        messages = [parent_message] + db.get(parent_message.childMessages)
        d = {}
        d['type'] = messages[0].TYPE
        d['messages'] = []
        for m in messages:
            sender_info = get_profile_info(m.sender, skip_warning=True)
            md = {
                'timestamp': m.creationTimestamp,
                'sender_name': sender_info.name if sender_info else None,
                'content':  m.message,
                'buttons': [],
                'attachments': []
            }
            for b in sorted(m.buttons or [], key=lambda x: x.index):
                bd = {
                    'id': b.id,
                    'caption': b.caption
                }
                md['buttons'].append(bd)

            for idx, a in enumerate(sorted(m.attachments or [], key=lambda x: x.index)):
                if a.content_type == AttachmentTO.CONTENT_TYPE_IMG_PNG:
                    filename = '%s.png' % idx
                elif a.content_type == AttachmentTO.CONTENT_TYPE_IMG_JPG:
                    filename = '%s.jpeg' % idx
                elif a.content_type == AttachmentTO.CONTENT_TYPE_PDF:
                    filename = '%s.pdf' % idx
                elif a.content_type == AttachmentTO.CONTENT_TYPE_VIDEO_MP4:
                    filename = '%s.mp4' % idx
                else:
                    filename = '%s' % idx
                download_path = os.path.join('messages', pmk, 'attachments', filename)
                yield ExportUserDownloadAttachmentPipeline(result_path, download_path, a.content_type, a.download_url)
                ad = {
                    'content_type': a.content_type,
                    'url': a.download_url,
                    'path': download_path,
                    'name': a.name
                }
                md['attachments'].append(ad)

            d['messages'].append(md)

        with cloudstorage.open(os.path.join(result_path, 'result', 'messages', pmk, 'messages.json'), 'w') as gcs_file:
            gcs_file.write(json.dumps(d))


class ExportUserMessagesPipeline(WorkloadPipeline):

    def run(self, result_path, human_user_email, app_id):
        app_user = create_app_user_by_email(human_user_email, app_id)
        for k in Message.all(keys_only=True).filter("member_status_index =", app_user.email()):
            if k.parent():
                continue
            yield ExportUserMessagePipeline(result_path, human_user_email, app_id, k.name())

        for k in ChatMembers.list_by_chat_member(app_user.email(), True):
            yield ExportUserMessagePipeline(result_path, human_user_email, app_id, k.parent().name())


class ExportUserProfilePipeline(WorkloadPipeline):

    def run(self, result_path, human_user_email, app_id):
        app_user = create_app_user_by_email(human_user_email, app_id)
        up = get_user_profile(app_user)

        if up and up.birthdate:
            birthdate = datetime.date.fromtimestamp(up.birthdate)
            birthday = {
                "year": birthdate.year,
                "month": birthdate.month,
                "day": birthdate.day
            }
        else:
            birthday = None

        with cloudstorage.open(os.path.join(result_path, 'result', 'profile', 'profile.json'), 'w') as gcs_file:
            gcs_file.write(json.dumps({
                'profile': {
                    'name': up.name if up else None,
                    'email': human_user_email,
                    'birthday': birthday,
                    'gender': up.gender_str if up else None,
                    'avatar_url': up.avatarUrl if up else None
                }
            }))
